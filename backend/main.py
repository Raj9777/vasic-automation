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

# --- ROBUST HEADERS (The Disguise) ---
# This makes your requests look like a real Chrome browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def extract_emails_from_text(text):
    # Improved Regex to catch more formats
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text, re.IGNORECASE)))

# --- 1. FAST SCAN (With Anti-Blocking Headers) ---
@app.post("/scan-website")
def scan_website(request: DomainRequest):
    # Ensure URL is clean
    domain = request.domain.replace("https://", "").replace("http://", "").strip("/")
    url = f"https://{domain}"
    
    try:
        # USE HEADERS HERE
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check if we were blocked (403/401)
        if response.status_code in [403, 401]:
             return {"status": "error", "message": "Website blocked our scanner (Security Check). Try Deep Search."}

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()
        emails = extract_emails_from_text(page_text)
        
        return {
            "status": "success",
            "source": "Website Scan",
            "emails": emails[:10],
            "meta_title": soup.title.string if soup.title else "No Title Found"
        }
    except Exception as e:
        return {"status": "error", "message": f"Scan failed: {str(e)}"}

# --- 2. DEEP SEARCH (Google API) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    # Strategy: Broad Search
    query = f'"{request.domain}" (email OR "contact" OR "mail to")'
    
    api_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 10
    }

    try:
        response = requests.get(api_url, params=params)
        data = response.json()

        if "error" in data:
            return {"status": "error", "message": "Google Quota Exceeded or Error."}

        found_emails = []
        snippets = []

        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                
                full_text = f"{title} {snippet}"
                extracted = extract_emails_from_text(full_text)
                
                # Clean and Add
                for email in extracted:
                    if request.domain in email.lower() or "gmail" in email.lower():
                        found_emails.append(email)
                
                snippets.append({"title": title, "link": link})

        return {
            "status": "success",
            "source": "Google Deep Search",
            "emails": list(set(found_emails)),
            "related_links": snippets
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}