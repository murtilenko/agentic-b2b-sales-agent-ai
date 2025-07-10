import os
import json
import openai
import re
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from utils.logger import logger
from dotenv import load_dotenv


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

CATALOG_PARSED = "data/catalog_parsed.json"
LEADS_PARSED = "data/leads_parsed.json"
WEBSITE_CONTENT_DIR = "data/website_content"
OUTPUT_DIR = "data/match_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
LIMIT = 20  # For testing

def combine_lead_text(lead, website_data):
    base = f"{lead.get('company_name', '')}. Notes: {lead.get('notes', '')}."
    if website_data:
        site_content = " ".join(website_data.values())[:1000]  # truncate
        base += f" Website Summary: {site_content}"
    return base.strip()


def format_product_catalog(products, limit=50):
    lines = []
    for idx, p in enumerate(products[:limit], 1):
        desc = f"{p['brand']} {p['product_name']} — {p['description'][:100]}".strip()
        lines.append(f"{idx}. {desc}")
    return "\n".join(lines)


def ask_gpt4o(lead_text, product_list_text):
    prompt = f"""
You are a product-fit analyst for B2B sales. Your goal is to identify the top 3 most relevant products from the list below for the company based on their website content.

Company Description:
{lead_text}

Product Catalog:
{product_list_text}

Instructions:
- Carefully review the website content and pick the 3 most relevant products.
- For each selected product, return:
  - brand
  - product_name
  - short reason for relevance

Return your response in this JSON format:
[
  {{
    "brand": "BrandName",
    "product_name": "Product Name",
    "reason": "Why it fits this company's business"
  }},
]
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT-4o error:", e)
        return ""
    
# def parse_llm_output(gpt_output: str, products: list) -> list:
#     try:
#         raw_matches = json.loads(gpt_output)
#     except Exception as e:
#         print("❌ Error parsing GPT output:", e)
#         return []
    
#     parsed = []
#     product_names_lower = {p["product_name"].lower(): p for p in products}

#     for item in raw_matches:
#         try:
#             name = item.get("product_name", "").lower()
#             brand = item.get("brand", "")
#             reason = item.get("reason", "")

#             # Attempt to match by product_name (case-insensitive)
#             matched_product = next((p for p in products if p["product_name"].lower() == name), None)
#             if matched_product:
#                 parsed.append({
#                     "product_name": matched_product["product_name"],
#                     "brand": matched_product["brand"],
#                     "score": 1.0,  # optional static score
#                     "reason": reason  # optional for logging/debugging
#                 })
#         except Exception as e:
#             print("⚠️ Failed to parse item:", item, e)
#             continue

#     return parsed

def extract_json_from_raw(raw_output: str):
    """
    Tries to extract a JSON block from GPT output.
    """
    try:
        # Look for a code block first
        code_block_match = re.search(r"```(?:json)?\s*(\[\s*{.*?}\s*])\s*```", raw_output, re.DOTALL)
        if code_block_match:
            return json.loads(code_block_match.group(1))
        
        # If no code block, try to find JSON array directly
        json_match = re.search(r"(\[\s*{.*?}\s*])", raw_output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Nothing found
        return []
    except Exception as e:
        print(f"❌ Error extracting JSON: {e}")
        return []

def match_products_to_leads():
    with open(CATALOG_PARSED, "r", encoding="utf-8") as f:
        products = json.load(f)
    with open(LEADS_PARSED, "r", encoding="utf-8") as f:
        leads = json.load(f)

    product_list_text = format_product_catalog(products)

    for lead in tqdm(leads[:LIMIT], desc="Matching companies"):
        company = lead["company_name"]
        safe_name = company.lower().replace(" ", "_").replace("/", "_")
        website_path = os.path.join(WEBSITE_CONTENT_DIR, f"{safe_name}.json")

        website_data = None
        if os.path.exists(website_path):
            with open(website_path, "r", encoding="utf-8") as f:
                website_data = json.load(f)

        lead_text = combine_lead_text(lead, website_data)

        results = {
            "company_name": company,
            "missing_website_data": website_data is None,
            "matches": {
                "gpt4o": []
            }
        }    

        # GPT-4o
        gpt_output = ask_gpt4o(lead_text, product_list_text)

        # Always store raw
        results["raw_gpt4o_output"] = gpt_output
        # Try to extract structured matches
        try:
            json_block = extract_json_from_raw(gpt_output)
            if json_block:
                results["matches"]["gpt4o"] = json_block
            else:
                raise ValueError("No JSON block found.")
        except Exception as e:
            print("❌ Error parsing GPT output:", e)
            print("⚠️ RAW GPT OUTPUT:", repr(gpt_output))
            results["matches"]["gpt4o"] = []
            results["raw_gpt4o_output"] = gpt_output

        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        with open(output_path, "w", encoding="utf-8") as f_out:
            json.dump(results, f_out, indent=2)

        print(f"✅ Saved results for {company} → {output_path}")

if __name__ == "__main__":
    match_products_to_leads()
