import os
import json
import datetime
import openai
from dotenv import load_dotenv
from utils.logger import logger
from utils.prompts import REPLY_ANALYSIS_PROMPT
from agent.memory_manager import update_conversation, mark_as_manual

# === Setup ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

EMAILS_DIR = "data/emails"
REPLIES_DIR = "data/replies"
MAX_ANALYSIS = 10  # Set how many leads to process

# === Loaders ===
def load_sent_emails():
    emails = {}
    for fname in os.listdir(EMAILS_DIR):
        if fname.endswith(".txt"):
            lead_id = fname.replace(".txt", "")
            with open(os.path.join(EMAILS_DIR, fname), "r", encoding="utf-8") as f:
                emails[lead_id] = f.read()
    return emails

def load_simulated_replies():
    replies = {}
    for fname in os.listdir(REPLIES_DIR):
        if fname.endswith(".txt"):
            lead_id = fname.replace(".txt", "")
            with open(os.path.join(REPLIES_DIR, fname), "r", encoding="utf-8") as f:
                replies[lead_id] = f.read()
    return replies

# === GPT Analyzer ===
def gpt_analyze_reply(sent_email: str, reply: str) -> dict:
    email_history = f"agent: {sent_email}\n\nlead: {reply}"
    prompt = REPLY_ANALYSIS_PROMPT.format(email_history=email_history)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Respond ONLY with a valid JSON object as specified in the prompt."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )
        raw = response.choices[0].message.content.strip()

        # Clean triple backtick wrappers
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        logger.info(f"📥 Cleaned GPT reply:\n{raw}")
        return json.loads(raw)
    except Exception as e:
        logger.error(f"❌ GPT analysis failed: {e}")
        return {"should_continue": False, "next_reply": None}

# === Helper: Save Analysis ===

def save_analysis_result(lead_id: str, analysis: dict):
    os.makedirs("data/analyzed_replies", exist_ok=True)
    file_path = os.path.join("data/analyzed_replies", f"{lead_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

# === Main ===
def run_analysis():
    sent_emails = load_sent_emails()
    simulated_replies = load_simulated_replies()
    processed = 0

    for lead_id in sent_emails:
        if lead_id not in simulated_replies:
            logger.warning(f"⚠️ No simulated reply found for lead: {lead_id}")
            continue

        if processed >= MAX_ANALYSIS:
            logger.info(f"✅ Limit of {MAX_ANALYSIS} leads reached. Stopping.")
            break

        sent = sent_emails[lead_id]
        reply = simulated_replies[lead_id]

        logger.info(f"🔍 Analyzing reply for: {lead_id}")
        analysis = gpt_analyze_reply(sent, reply)
        save_analysis_result(lead_id, analysis)

        # Build conversation
        conversation = [
            {
                "sender": "agent",
                "content": sent,
                "timestamp": str(datetime.datetime.utcnow())
            },
            {
                "sender": "lead",
                "content": reply,
                "timestamp": str(datetime.datetime.utcnow())
            }
        ]

        if not analysis.get("should_continue"):
            logger.info(f"🛑 Conversation for {lead_id} marked for manual handling.")
            mark_as_manual(lead_id)
        else:
            followup = analysis.get("next_reply", "")
            logger.info(f"🤖 GPT suggests reply:\n{followup}")
            conversation.append({
                "sender": "agent",
                "content": followup,
                "timestamp": str(datetime.datetime.utcnow())
            })

        # Save conversation state
        update_conversation(lead_id, conversation, {
            "last_transaction_type": "sent_email" if analysis.get("should_continue") else "received_email",
            "turned_to_manual": not analysis.get("should_continue"),
            "turned_to_manual_at": str(datetime.datetime.utcnow()) if not analysis.get("should_continue") else None
        })

        processed += 1

if __name__ == "__main__":
    run_analysis()
