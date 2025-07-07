import os
import json
import pandas as pd

# Define paths
LEADS_PATH = "data/leads_info.xlsx"
PROCESSED_DIR = "data"
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "leads_parsed.json")

def load_leads(leads_path):
    df = pd.read_excel(leads_path)

    leads = []
    for _, row in df.iterrows():
        lead = {
            "company_name": str(row.get("company_name", "")).strip(),
            "website": str(row.get("website", "")).strip(),
            "contact_name": str(row.get("contact_name", "")).strip(),
            "contact_email": str(row.get("contact_email", "")).strip(),
            "notes": str(row.get("notes", "")).strip()
        }
        leads.append(lead)

    return leads

def save_parsed_leads(leads):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)
    print(f"✅ Parsed leads saved to: {OUTPUT_FILE}")

# Optional test trigger
if __name__ == "__main__":
    parsed_leads = load_leads(LEADS_PATH)
    save_parsed_leads(parsed_leads)
