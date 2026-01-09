import os
import requests
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

class DomainRequest(BaseModel):
    domain: str

# Helper: Simple Email Regex
def extract_emails_from_text(text):
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))

# --- 1. FAST SCAN (Website Scraper) ---
@app.post("/scan-website")
def scan_website(request: DomainRequest):
    url = f"https://{request.domain}" if not request.domain.startswith("http") else request.domain
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        page_text = soup.get_text()
        emails = extract_emails_from_text(page_text)
        
        return {
            "status": "success",
            "source": "Website Scan",
            "emails": emails[:5],
            "meta_title": soup.title.string if soup.title else "No Title Found"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 2. DEEP SEARCH (Google API) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    # The Optimized Query
    query = f'site:linkedin.com/in/ OR site:{request.domain} "{request.domain}" "email" "@ {request.domain}" (CEO OR Founder)'
    
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
            print("Google API Error:", data["error"])
            return {"status": "error", "message": "Search quota exceeded or API error."}

        found_emails = []
        snippets = []

        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                
                full_text = f"{title} {snippet}"
                extracted = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text, re.IGNORECASE)
                
                # Filter for target domain
                valid_emails = [e for e in extracted if request.domain in e.lower()]
                
                found_emails.extend(valid_emails)
                snippets.append({"title": title, "link": link})

        return {
            "status": "success",
            "source": "Google Deep Search",
            "emails": list(set(found_emails)),
            "related_links": snippets
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}