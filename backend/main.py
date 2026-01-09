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

# Disguise requests as a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

def extract_emails_from_text(text):
    # Standard Regex for any email address
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text, re.IGNORECASE)))

def extract_emails_from_html(soup):
    emails = set()
    
    # 1. MAILTO: Look for 'mailto:' links (High Accuracy)
    for a in soup.find_all('a', href=True):
        if "mailto:" in a['href']:
            clean_email = a['href'].replace("mailto:", "").split("?")[0]
            emails.add(clean_email)

    # 2. TEXT: Look for text patterns (Broad Catch)
    text_emails = extract_emails_from_text(soup.get_text())
    for email in text_emails:
        emails.add(email)
        
    return list(emails)

# --- 1. SMART FAST SCAN (Unrestricted) ---
@app.post("/scan-website")
def scan_website(request: DomainRequest):
    domain = request.domain.replace("https://", "").replace("http://", "").strip("/")
    base_url = f"https://{domain}"
    
    found_emails = []
    # Auto-check Home, Contact, About
    pages_to_check = [base_url, f"{base_url}/contact", f"{base_url}/about"]
    
    try:
        for url in pages_to_check:
            try:
                # print(f"Scanning: {url}") # Uncomment for debugging logs
                response = requests.get(url, headers=HEADERS, timeout=5)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    emails = extract_emails_from_html(soup)
                    
                    if emails:
                        found_emails.extend(emails)
                        # We don't break here anymore, we scan ALL pages to get MAX emails
            except:
                continue

        return {
            "status": "success",
            "source": "Smart Website Scan",
            "emails": list(set(found_emails))[:15], # Increased limit
            "meta_title": f"Scanned {domain}"
        }

    except Exception as e:
        return {"status": "error", "message": f"Scan failed: {str(e)}"}

# --- 2. DEEP SEARCH (Unrestricted) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    # Query: Look for any email associated with the domain
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
                
                full_text = f"{title} {snippet}"
                extracted = extract_emails_from_text(full_text)
                
                # --- CHANGE IS HERE ---
                # We removed the 'if domain in email' filter.
                # Now we accept EVERYTHING.
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