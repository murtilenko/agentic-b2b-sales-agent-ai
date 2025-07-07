
import os
import json
import pandas as pd

# Define the paths
CATALOG_PATH = "data/product_info.xlsx"
PROCESSED_DIR = "data"
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "catalog_parsed.json")

def load_product_catalog(catalog_path):
    df = pd.read_excel(catalog_path)

    products = []
    for _, row in df.iterrows():
        product = {
            "brand": str(row.get("brand_name", "")).strip(),
            "product_name": str(row.get("product_name", "")).strip(),
            "description": str(row.get("description", "")).strip(),
            "target_industries": [i.strip() for i in str(row.get("target_industries", "")).split(",")],
            "target_product_types": [i.strip() for i in str(row.get("target_product_types", "")).split(",")],
            "keywords": [k.strip() for k in str(row.get("keywords", "")).split(",")]
        }
        products.append(product)

    return products

def save_parsed_catalog(products):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    print(f"✅ Parsed catalog saved to: {OUTPUT_FILE}")

# Optional main trigger to test
if __name__ == "__main__":
    parsed = load_product_catalog(CATALOG_PATH)
    save_parsed_catalog(parsed)
