import os
import json
import openai
from agent.utils.prompts import SALES_EMAIL_PROMPT
from agent.utils.logger import logger

# === Config ===
MATCH_RESULTS_DIR = "data/match_results"
OUTPUT_DIR = "data/emails"
COMPANY_INFO_FILE = "data/company_info.md"
USE_GPT = False # 🔄 Set to False to use offline generation
LIMIT = 1       # 🔁 Limit number of companies for testing

# === Setup ===
os.makedirs(OUTPUT_DIR, exist_ok=True)
openai.api_key = os.getenv("OPENAI_API_KEY")


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_match_results():
    files = sorted(os.listdir(MATCH_RESULTS_DIR))
    jsons = []
    for f in files:
        if f.endswith(".json"):
            with open(os.path.join(MATCH_RESULTS_DIR, f), "r", encoding="utf-8") as f_json:
                jsons.append(json.load(f_json))
    return jsons[:LIMIT]


def build_prompt(company_data, company_info):
    company_name = company_data["company_name"]
    matched = company_data.get("matched_products", [])
    product_list = "\n".join(
        [f"- {p['brand']} {p['product_name']} (score: {p['score']})" for p in matched]
    ) or "None"

    return SALES_EMAIL_PROMPT.format(
        company_name=company_name,
        company_info=company_info,
        product_list=product_list
    )


def generate_email(prompt):
    if USE_GPT:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional B2B sales assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response["choices"][0]["message"]["content"]
    else:
        return "[OFFLINE MODE]\n\nDear [Company],\n\nWe thought your business might benefit from some of our packaging solutions. Let us know if you’d like to explore this further.\n\nBest regards,\n[Your Name]"


def write_email(company_name, content):
    safe_name = company_name.lower().replace(" ", "_").replace("/", "_")
    output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(content)
    print(f"📧 Email saved for {company_name} → {output_path}")


def main():
    company_info = load_text(COMPANY_INFO_FILE)
    match_results = load_match_results()

    for entry in match_results:
        company = entry["company_name"]
        prompt = build_prompt(entry, company_info)
        email = generate_email(prompt)
        write_email(company, email)


if __name__ == "__main__":
    main()
