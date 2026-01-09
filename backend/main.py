import os
import requests
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

class DomainRequest(BaseModel):
    domain: str

# Headers to look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

def extract_emails_from_html(soup):
    emails = set()
    
    # 1. SEARCH: Look for 'mailto:' links (The most accurate method)
    for a in soup.find_all('a', href=True):
        if "mailto:" in a['href']:
            # Clean the mailto link (remove 'mailto:' and params like '?subject=...')
            clean_email = a['href'].replace("mailto:", "").split("?")[0]
            emails.add(clean_email)

    # 2. SEARCH: Look for text patterns in the visible page
    text_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", soup.get_text(), re.IGNORECASE)
    for email in text_emails:
        emails.add(email)
        
    return list(emails)

# --- 1. SMART FAST SCAN ---
@app.post("/scan-website")
def scan_website(request: DomainRequest):
    domain = request.domain.replace("https://", "").replace("http://", "").strip("/")
    base_url = f"https://{domain}"
    
    found_emails = []
    pages_to_check = [base_url, f"{base_url}/contact", f"{base_url}/about", f"{base_url}/contact-us"]
    
    try:
        # Loop through Home, Contact, and About pages until we find emails
        for url in pages_to_check:
            try:
                print(f"Scanning: {url}")
                response = requests.get(url, headers=HEADERS, timeout=5)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    emails = extract_emails_from_html(soup)
                    
                    if emails:
                        found_emails.extend(emails)
                        # If we found emails, stop scanning other pages to save time
                        break
            except:
                continue # If a page doesn't exist (e.g. /contact-us), just skip it

        return {
            "status": "success",
            "source": "Smart Website Scan",
            "emails": list(set(found_emails))[:10], # Remove duplicates
            "meta_title": f"Scanned {domain}"
        }

    except Exception as e:
        return {"status": "error", "message": f"Scan failed: {str(e)}"}

# --- 2. DEEP SEARCH (Google API) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    query = f'"{request.domain}" (email OR "contact")'
    
    api_url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "num": 10}

    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        
        found_emails = []
        snippets = []

        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                
                # Combine and extract
                full_text = f"{title} {snippet}"
                extracted = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text, re.IGNORECASE)
                
                found_emails.extend(extracted)
                snippets.append({"title": title, "link": link})

        return {
            "status": "success",
            "source": "Google Deep Search",
            "emails": list(set(found_emails)),
            "related_links": snippets
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}