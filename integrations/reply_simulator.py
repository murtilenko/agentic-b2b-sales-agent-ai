import os
import openai
import random
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables and OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

EMAILS_DIR = "data/emails"
REPLIES_DIR = "data/replies"
MAX_LEADS = 6  # Set a limit for simulation runs

# Ensure replies directory exists
os.makedirs(REPLIES_DIR, exist_ok=True)

# Load all previously sent emails
def load_sent_emails():
    email_data = {}
    for fname in os.listdir(EMAILS_DIR):
        if fname.endswith(".txt"):
            lead_id = fname.replace(".txt", "")
            with open(os.path.join(EMAILS_DIR, fname), "r", encoding="utf-8") as f:
                content = f.read()
                email_data[lead_id] = content
    return email_data

# Simulate customer reply using GPT
def simulate_reply(sent_email: str) -> str:
    tone = random.choice(["positive", "curious", "suspicious", "negative"])
    prompt = f"""
You are roleplaying as a B2B packaging buyer receiving an unsolicited email from a packaging supplier.

Here is the email you received:
---
{sent_email}
---

Write a realistic reply from the buyer with a **{tone}** tone:
- If positive: express interest, ask follow-up questions, request pricing/timeline
- If negative: politely decline or say not interested
- If suspicious: ask skeptical questions, delay decision, request proof or references

ONLY respond with the buyer's reply. No tone label, no explanation.

Make sure your reply feels like a real B2B message, not fictional or dramatic. Include a question or comment that fits your chosen tone.
Only output the reply text — do not label the tone or explain anything.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=200
        )
        reply = response.choices[0].message.content.strip()
        return reply
    except Exception as e:
        logger.error(f"❌ GPT simulation failed: {e}")
        return None

# Save simulated reply
def save_simulated_reply(lead_id: str, reply: str):
    path = os.path.join(REPLIES_DIR, f"{lead_id}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(reply)

# Main loop
def run_simulator():
    sent_emails = load_sent_emails()
    processed = 0

    for lead_id, sent_email in sent_emails.items():
        if processed >= MAX_LEADS:
            logger.info(f"✅ Limit of {MAX_LEADS} leads reached. Stopping.")
            break

        logger.info(f"📤 Simulating reply for: {lead_id}")
        reply = simulate_reply(sent_email)

        if reply:
            logger.info(f"📨 Simulated reply:\n{reply}")
            save_simulated_reply(lead_id, reply)
        else:
            logger.warning(f"⚠️ Skipped {lead_id} due to simulation failure.")

        processed += 1

if __name__ == "__main__":
    run_simulator()
