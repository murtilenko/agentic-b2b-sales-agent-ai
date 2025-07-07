import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from agent.utils.logger import logger


# Configuration
LEADS_FILE = "data/leads_parsed.json"
OUTPUT_DIR = "data/website_content"
LIMIT = 10  # Max number of leads to crawl

# Make sure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Target subpages
TARGET_PAGES = {
    "home": ["/", "/home", "/index"],
    "about": [
        "about", "about-us", "company", "our-company", "who-we-are", "our-story", "mission", "vision",
        "company-info", "aboutus", "history", "team", "leadership"
    ],
    "products": [
        "products", "product", "catalog", "what-we-offer", "product-line", "product-range",
        "our-products", "inventory", "shop", "product-catalog"
    ],
    "services": [
        "services", "service", "solutions", "offerings", "what-we-do", "capabilities",
        "consulting", "logistics", "fulfillment", "support", "specialties"
    ]
}


def fetch_text_from_url(url):
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
    return ""


def crawl_website(base_url):
    result = {}
    for page_type, paths in TARGET_PAGES.items():
        for path in paths:
            full_url = urljoin(base_url, path)
            print(f"🔍 Trying {full_url}")
            content = fetch_text_from_url(full_url)
            if content and len(content) > 100:
                result[page_type] = content
                break  # stop once we get a valid page for that type
    return result


def crawl_leads(limit=LIMIT):
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        leads = json.load(f)

    for i, lead in enumerate(leads[:limit]):
        company = lead.get("company_name", f"company_{i}")
        website = lead.get("website")

        if not website:
            continue
        
        print(f"\n🌐 Crawling: {company} ({website})")
        safe_name = company.lower().replace(" ", "_").replace("/", "_")
        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        
        if os.path.exists(output_path):
                print(f"⏩ Skipping {company}, already crawled.")
                continue
        
        cleaned_url = website.strip()
        if not cleaned_url.startswith("http"):
            cleaned_url = "https://" + cleaned_url

        site_content = crawl_website(cleaned_url)

        if site_content:
            safe_name = company.lower().replace(" ", "_").replace("/", "_")
            output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
            with open(output_path, "w", encoding="utf-8") as f_out:
                json.dump(site_content, f_out, indent=2)
            print(f"✅ Saved content for {company} to {output_path}")
        else:
            print(f"⚠️ No content extracted for {company}")


if __name__ == "__main__":
    crawl_leads()
