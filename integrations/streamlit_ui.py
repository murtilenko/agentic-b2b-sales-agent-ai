import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
import random
import json
import glob
from dotenv import load_dotenv
from agent.catalog_loader import load_product_catalog, save_parsed_catalog
from agent.lead_loader import load_leads, save_parsed_leads
from agent.product_matcher import match_products_to_leads
from agent.email_writer import main as email_writer
from integrations.email_sender import send_all_emails as email_sender
from integrations.reply_analyzer import run_analysis as reply_analyzer
from integrations.reply_simulator import run_simulator as reply_simulator
from agent.web_crawler import crawl_leads as web_crawler

load_dotenv()

# --- Auto-load Excel files from disk if present ---
#if os.path.exists("data/product_info.xlsx") and os.path.exists("data/leads_info.xlsx"):
 #   st.session_state.catalog_df = pd.read_excel("data/product_info.xlsx")
  #  st.session_state.leads_df = pd.read_excel("data/leads_info.xlsx")

# Initialize session state variables
if "catalog_df" not in st.session_state:
    st.session_state.catalog_df = None
if "leads_df" not in st.session_state:
    st.session_state.leads_df = None
if "matches" not in st.session_state:
    st.session_state.matches = []
if "selected_lead_index" not in st.session_state:
    st.session_state.selected_lead_index = None
if "generated_email" not in st.session_state:
    st.session_state.generated_email = ""
if "crawler_ran" not in st.session_state:
    st.session_state.crawler_ran = False

st.title("🤖 B2B Outreach AI Agent")

# --- Step 1: Load Catalog & Leads ---

st.header("1. Load Product Catalog & Leads")

catalog_file = st.file_uploader("Upload Product Catalog Excel", type=["xlsx"])
if catalog_file:
    with open("data/product_info.xlsx", "wb") as f:
        f.write(catalog_file.getbuffer())
    st.success("Catalog saved to data/product_info.xlsx")

leads_file = st.file_uploader("Upload Leads Excel", type=["xlsx"])
if leads_file and not st.session_state.crawler_ran:
    with open("data/leads_info.xlsx", "wb") as f:
        f.write(leads_file.getbuffer())
    st.success("Leads saved to data/leads_info.xlsx")

    catalog_path = "data/product_info.xlsx"
    leads_path = "data/leads_info.xlsx"   
    if os.path.exists(catalog_path) and os.path.exists(leads_path):

        catalog = load_product_catalog(catalog_path)
        save_parsed_catalog(catalog)

        leads = load_leads(leads_path)
        save_parsed_leads(leads)

        web_crawler()  # Run web crawler to fetch website content

         # ✅ Update session state
        st.session_state.catalog_df = pd.read_excel(catalog_path)
        st.session_state.leads_df = pd.read_excel(leads_path)
        st.session_state.crawler_ran = True

        st.success("✅ Catalog and Leads successfully parsed and saved to JSON.")
    else:
        st.error("❌ Required Excel files not found in `data/` directory.")


# --- Debug: Show Columns in Catalog and Leads DataFrames ---

if st.button("Show Catalog and Leads Columns"):
    if st.session_state.catalog_df is not None:
        st.write("Catalog columns:", st.session_state.catalog_df.columns.tolist())
    else:
        st.write("Catalog DataFrame is empty.")

    if st.session_state.leads_df is not None:
        st.write("Leads columns:", st.session_state.leads_df.columns.tolist())
    else:
        st.write("Leads DataFrame is empty.")

# --- Step 2: Match Products to Leads ---

st.header("2. Match Products to Leads")

if st.session_state.catalog_df is None or st.session_state.leads_df is None:
    st.warning("Please load both catalog and leads first.")
else:
    if st.button("Run Product Matching"):
        with st.spinner("Running your product matcher..."):
            try:
                from agent.product_matcher import match_products_to_leads
                match_products_to_leads()
                st.success("✅ Product matching completed. Results saved in `data/match_results/`.")
            except Exception as e:
                st.error(f"❌ Error during product matching: {e}")

# --- Step 3: Select Lead and Generate Email ---

st.header("3. Generate Outreach Emails")

if not os.path.exists("data/match_results"):
    st.warning("Please run product matching first to generate leads.")
else:
    if st.button("Generate Emails"):
        try:
            with st.spinner("Generating emails using email_writer.main()..."):
                email_writer()
            st.success("✅ Emails generated successfully!")
        except Exception as e:
            st.error(f"❌ Error generating emails: {e}")
            
        
# --- Step 4: Simulate and Classify Reply ---

st.header("4. Simulate and Classify Reply")

if not os.path.exists("data/emails"):
    st.warning("Please run product matching first to generate leads.")
else:
    if st.button("Simulate and Classify Reply"):
        with st.spinner("Mr Robot Working on It."):
            reply_simulator()
            reply_analyzer()
            st.success("Done!")

# --- Step 5: Send Emails to All Leads ---
st.header("5. Send Emails to All Leads")

if not os.path.exists("data/emails"):
    st.warning("Please run product matching first to generate leads.")
else:
    if st.button("Send Emails to All Leads"):
        email_sender()
        st.success("✅ Emails sent to all leads!")

# --- Step 6: Show Random Lead Interaction ---
st.header("6. Show Random Lead Interaction")

if st.button("Show Random Results"):
    match_files = glob.glob("data/match_results/*.json")
    if not match_files:
        st.warning("No match results found in data/match_results/")
    else:
        random_file = random.choice(match_files)
        company_name = os.path.splitext(os.path.basename(random_file))[0]
        st.subheader(f"🧠 Company: {company_name}")

        # Load and show matched product info
        product_path = f"data/match_results/{company_name}.json"
        if os.path.exists(product_path):
            with open(product_path, "r", encoding="utf-8") as f:
                product_text = f.read()
            st.markdown("### Match Products")
            st.text_area("Products", product_text, height=250)
        else:
            st.info("Product not found for this company.")

        # Load and show generated email
        email_path = f"data/emails/{company_name}.txt"
        if os.path.exists(email_path):
            with open(email_path, "r", encoding="utf-8") as f:
                email_text = f.read()
            st.markdown("### 📧 Generated Email")
            st.text_area("Email", email_text, height=250)
        else:
            st.info("Email not found for this company.")

        # Load and show simulated reply
        reply_path = f"data/replies/{company_name}.txt"
        if os.path.exists(reply_path):
            with open(reply_path, "r", encoding="utf-8") as f:
                reply_text = f.read()
            st.markdown("### 🤖 Simulated Reply")
            st.text_area("Reply", reply_text, height=250)
        else:
            st.info("Simulated reply not found.")

        # Load and show analyzed reply
        analysis_path = f"data/analyzed_replies/{company_name}.json"
        if os.path.exists(analysis_path):
            with open(analysis_path, "r", encoding="utf-8") as f:
                analysis_data = json.load(f)
            st.markdown("### 🧪 Reply Analysis")
            st.json(analysis_data)
        else:
            st.info("Reply analysis not found.")