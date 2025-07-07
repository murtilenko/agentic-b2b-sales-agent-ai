import os
import json
import openai
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from agent.utils.logger import logger

CATALOG_PARSED = "data/catalog_parsed.json"
LEADS_PARSED = "data/leads_parsed.json"
WEBSITE_CONTENT_DIR = "data/website_content"
OUTPUT_DIR = "data/match_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
LIMIT = 1  # For testing

# Load LLaMA-style local model
llama_model_id = "mistralai/Mistral-7B-Instruct-v0.2"
llama_tokenizer = AutoTokenizer.from_pretrained(llama_model_id)
llama_model = AutoModelForCausalLM.from_pretrained(llama_model_id)
llama_pipeline = pipeline("text-generation", model=llama_model, tokenizer=llama_tokenizer, max_new_tokens=256)


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
Company Description:
{lead_text}

Product Catalog:
{product_list_text}

Based on the company's business and website, choose the top 5 products that best match their needs.
Respond with this format:
1. [Product Name] — [Score 0.0–1.0]
2. ...
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


def ask_llama3(lead_text, product_list_text):
    prompt = f"""
Company: {lead_text}

Catalog:
{product_list_text}

Please list the 5 most relevant products to the company and assign a confidence score from 0.0 to 1.0.
Example:
1. Brownie Tray — 0.91
2. Pizza Box — 0.85
"""
    try:
        result = llama_pipeline(prompt)[0]["generated_text"]
        return result.strip().split("\n")[-6:]  # get last lines
    except Exception as e:
        print("❌ LLaMA3 error:", e)
        return []


def parse_llm_output(output_lines, products):
    parsed = []
    names = {p["product_name"].lower(): p for p in products}
    for line in output_lines:
        try:
            if "—" in line:
                parts = line.strip().split("—")
                name = parts[0].split(".")[-1].strip()
                score = round(float(parts[1].strip()), 3)
                # match by name
                for p in products:
                    if name.lower() in p["product_name"].lower():
                        parsed.append({
                            "product_name": p["product_name"],
                            "brand": p["brand"],
                            "score": score
                        })
                        break
        except:
            continue
    return parsed


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
                "gpt4o": [],
                "llama3": []
            }
        }

        # GPT-4o
        gpt_output = ask_gpt4o(lead_text, product_list_text)
        results["matches"]["gpt4o"] = parse_llm_output(gpt_output.splitlines(), products)

        # LLaMA3
        llama_output = ask_llama3(lead_text, product_list_text)
        results["matches"]["llama3"] = parse_llm_output(llama_output, products)

        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        with open(output_path, "w", encoding="utf-8") as f_out:
            json.dump(results, f_out, indent=2)

        print(f"✅ Saved results for {company} → {output_path}")


if __name__ == "__main__":
    match_products_to_leads()
