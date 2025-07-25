import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

# === Config ===
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # Your sender email
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # App password or real password (if less secure apps enabled)
EMAILS_DIR = "data/emails"
LEADS_FILE = "data/leads_parsed.json"
LIMIT = 2  # 🔁 Only send to this many leads

# === Load leads ===
def load_leads():
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# === Send one email ===
def send_email(to_email, subject, body, lead_id=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"✅ Email sent to {to_email} (lead: {lead_id})")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email} (lead: {lead_id}): {e}")
        return False

# === Load and Send All Emails (with LIMIT) ===
def send_all_emails():
    leads = load_leads()
    count = 0

    for lead in leads:
        if LIMIT is not None and count >= LIMIT:
            break

        company_name = lead["company_name"]
        contact_email = lead["contact_email"]

        if not contact_email:
            logger.warning(f"⚠️ No email for {company_name}, skipping.")
            continue

        safe_name = company_name.lower().replace(" ", "_").replace("/", "_")
        email_file = os.path.join(EMAILS_DIR, f"{safe_name}.txt")

        if not os.path.exists(email_file):
            logger.warning(f"⚠️ No email content found for {company_name}, skipping.")
            continue

        with open(email_file, "r", encoding="utf-8") as f:
            email_body = f.read()

        subject = f"Packaging Solutions for {company_name} [LeadID: {safe_name}]"

        if send_email(contact_email, subject, email_body, lead_id=safe_name):
            count += 1

# === Run as script ===
if __name__ == "__main__":
    send_all_emails()
