import os
import datetime
from agent.reply_handler import handle_incoming_reply

EMAILS_DIR = "data/emails"


# === Step 1: Load initial emails from email_writer output ===
def load_initial_emails():
    initial_data = {}
    for fname in os.listdir(EMAILS_DIR):
        if fname.endswith(".txt"):
            lead_id = fname.replace(".txt", "")
            with open(os.path.join(EMAILS_DIR, fname), "r", encoding="utf-8") as f:
                initial_content = f.read()
                initial_data[lead_id] = [
                    {
                        "sender": "agent",
                        "content": initial_content,
                        "timestamp": str(datetime.datetime.utcnow())
                    }
                ]
    return initial_data

initial_conversations = load_initial_emails()

# === Step 2: Mock replies to test ===
mock_replies = {
    "kariout": [
        "Thank you for reaching out. We’re definitely interested in learning more about your packaging solutions. Could you please provide a detailed price sheet and information on your standard lead times? Additionally, do you offer custom branding options or support for eco-friendly certifications? Looking forward to your response."
    ],
    "fiori_bruno_pasta": [
        "Not interested at this time, thanks."
    ]
}

# === Step 3: Simulate the replies ===
for lead_id, replies in mock_replies.items():
    for reply in replies:
        print(f"\n📨 Incoming reply from {lead_id}: {reply}")
        followup = handle_incoming_reply(lead_id, reply)
        if followup:
            print(f"🤖 GPT Suggested Follow-up:\n{followup}")
        else:
            print(f"🛑 Conversation with {lead_id} marked as manual.")
