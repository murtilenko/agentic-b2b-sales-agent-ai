import openai
import datetime
from agent.memory_manager import get_conversation, update_conversation, mark_as_manual
from agent.utils.logger import logger
from agent.utils.prompts import REPLY_ANALYSIS_PROMPT


def gpt_analyze_reply(conversation_history: list, latest_reply: str) -> dict:
    """Analyze the reply and return intent and recommended next action."""
    formatted_history = "\n\n".join(
        [f"{msg['sender']}: {msg['content']}" for msg in conversation_history]
    )
    prompt = REPLY_ANALYSIS_PROMPT.format(
        conversation_history=formatted_history,
        latest_reply=latest_reply
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"GPT-4o analysis failed: {e}")
        return {
            "continue": False,
            "suggested_reply": None
        }


def handle_incoming_reply(lead_id: str, incoming_text: str):
    logger.info(f"📨 New reply received for lead: {lead_id}")

    # Load existing conversation
    conversation = get_conversation(lead_id)
    conversation.append({
        "sender": "lead",
        "content": incoming_text,
        "timestamp": str(datetime.datetime.utcnow())
    })

    # Analyze intent using GPT
    result = gpt_analyze_reply(conversation, incoming_text)

    if not result["continue"]:
        logger.info(f"🛑 Thread for {lead_id} marked for manual handling.")
        mark_as_manual(lead_id)
        update_conversation(lead_id, conversation, {
            "last_transaction_type": "received_email",
            "turned_to_manual": True,
            "turned_to_manual_at": str(datetime.datetime.utcnow())
        })
        return

    # Continue with GPT-generated reply
    followup = result["suggested_reply"]
    logger.info(f"🤖 GPT suggests follow-up for {lead_id}: {followup}")

    conversation.append({
        "sender": "agent",
        "content": followup,
        "timestamp": str(datetime.datetime.utcnow())
    })

    update_conversation(lead_id, conversation, {
        "last_transaction_type": "sent_email"
    })

    # You would pass `followup` to your actual email sending function here
    return followup  # Optional: return for testing
