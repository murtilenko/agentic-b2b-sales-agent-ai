import openai
import datetime
from agent.memory_manager import get_conversation, update_conversation, mark_as_manual
from agent.utils.logger import logger


def gpt_analyze_reply(conversation_history: list, latest_reply: str) -> dict:
    """Analyze the reply and return intent and recommended next action."""
    formatted_history = "\n\n".join(
        [f"{msg['sender']}: {msg['content']}" for msg in conversation_history]
    )
    prompt = f"""You are an intelligent B2B sales assistant. Here is the recent email thread:

{formatted_history}

The latest reply from the customer is:
"{latest_reply}"

Analyze the customer's intent and suggest:
1. Whether to continue the conversation or not (yes/no)
2. A suggested follow-up message (if continuing)

Reply in JSON format like:
{{
  "continue": true,
  "suggested_reply": "Thanks for your interest! Here’s more info..."
}}"""

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
