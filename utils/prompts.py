# agent/utils/prompts.py

# SALES EMAIL PROMPT
SALES_EMAIL_PROMPT = """
You are an expert B2B sales assistant helping a packaging manufacturer reach out to potential business leads.

Here is background information about our company and product line:
---
{company_info}
---

Here is information about the target lead:
---
Company Name: {lead_company}
Website Text:
{lead_website}
---

Please write a short and engaging outreach email to this company offering our packaging solutions.
- Be professional but friendly
- Reference their industry or product needs if possible
- Keep it under 200 words
- Use a real-sounding human tone, not robotic
- Avoid being pushy or too generic
- Mention that a product catalog PDF is attached
- End with a soft CTA (e.g., “We’d love to explore how we can support your packaging needs.”)

Output only the **body of the email**, without greeting headers like "Subject:".
"""

# REPLY INTENT ANALYSIS PROMPT
REPLY_ANALYSIS_PROMPT = """
You are analyzing an email thread between a packaging supplier and a potential business lead.

Here is the conversation history:
---
{email_history}
---

Please analyze the most recent reply from the lead. Answer the following:

1. What is the intent of the lead’s reply? (e.g., interested, not interested, asking for pricing, generic response, bounce, unsubscribe, etc.)

2. Should the AI assistant continue the conversation? (yes or no)

3. If yes, what would be a natural and helpful next reply? Draft it accordingly.
4. If no, briefly explain why and stop the conversation.

Output as structured JSON with fields:
- "intent"
- "should_continue"
- "next_reply" (only if should_continue is yes)
"""