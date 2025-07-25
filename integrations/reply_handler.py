import os
import datetime
import base64
import json
import openai
from email import message_from_bytes
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from agent.memory_manager import get_conversation, update_conversation, mark_as_manual
from utils.logger import logger
from utils.prompts import REPLY_ANALYSIS_PROMPT

# === Load env and OpenAI API Key ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Gmail API Setup ===
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = 'token.json'

def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build('gmail', 'v1', credentials=creds)

def fetch_recent_replies(service, query="is:inbox is:unread"):
    response = service.users().messages().list(userId='me', q=query).execute()
    messages = response.get('messages', [])
    replies = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        parts = msg_data['payload'].get('parts', [])
        payload = msg_data['payload'].get('body', {})
        body_data = None

        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body'].get('data')
                    break
        elif payload.get('data'):
            body_data = payload['data']

        if body_data:
            decoded = base64.urlsafe_b64decode(body_data).decode('utf-8')
            replies.append({
                "from": from_email,
                "subject": subject,
                "body": decoded.strip()
            })

    return replies

# === GPT-4o Intent Analysis ===
def gpt_analyze_reply(conversation_history, latest_reply):
    formatted_history = "\n\n".join([f"{msg['sender']}: {msg['content']}" for msg in conversation_history])
    prompt = REPLY_ANALYSIS_PROMPT.format(email_history=formatted_history, latest_reply=latest_reply)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"GPT analysis failed: {e}")
        return {
            "intent": "error",
            "should_continue": False,
            "next_reply": None
        }

# === Handler ===
def handle_incoming_reply(lead_id: str, incoming_text: str):
    logger.info(f"📨 New reply received for lead: {lead_id}")
    conversation = get_conversation(lead_id)
    conversation.append({
        "sender": "lead",
        "content": incoming_text,
        "timestamp": str(datetime.datetime.utcnow())
    })

    result = gpt_analyze_reply(conversation, incoming_text)

    if not result["should_continue"]:
        logger.info(f"🛑 Marking thread for {lead_id} as manual.")
        mark_as_manual(lead_id)
        update_conversation(lead_id, conversation, {
            "last_transaction_type": "received_email",
            "turned_to_manual": True,
            "turned_to_manual_at": str(datetime.datetime.utcnow())
        })
        return

    reply_text = result["next_reply"]
    logger.info(f"🤖 GPT suggests follow-up for {lead_id}: {reply_text}")
    conversation.append({
        "sender": "agent",
        "content": reply_text,
        "timestamp": str(datetime.datetime.utcnow())
    })

    update_conversation(lead_id, conversation, {
        "last_transaction_type": "sent_email"
    })

    return reply_text

# === Main Runner ===
if __name__ == "__main__":
    gmail = get_gmail_service()
    incoming = fetch_recent_replies(gmail)

    for reply in incoming:
        from_email = reply["from"]
        reply_body = reply["body"]

        # Derive lead_id from email address for simplicity
        lead_id = from_email.split('@')[0].lower().replace(".", "_").replace("-", "_")

        followup = handle_incoming_reply(lead_id, reply_body)
        if followup:
            print(f"✅ GPT Response for {lead_id}:\n{followup}\n")
        else:
            print(f"🛑 {lead_id} marked as manual.")
