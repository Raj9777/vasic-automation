import os
import requests
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

# Enable CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# Load keys from Environment Variables (Set these in Render Dashboard)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

class DomainRequest(BaseModel):
    domain: str

# Helper: Simple Email Regex
def extract_emails_from_text(text):
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))

# --- 1. FAST SCAN (Scrapes the Website directly) ---
@app.post("/scan-website")
def scan_website(request: DomainRequest):
    url = f"https://{request.domain}" if not request.domain.startswith("http") else request.domain
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract text and find emails
        page_text = soup.get_text()
        emails = extract_emails_from_text(page_text)
        
        return {
            "status": "success",
            "source": "Website Scan",
            "emails": emails[:5],  # Limit to top 5
            "meta_title": soup.title.string if soup.title else "No Title Found"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 2. DEEP SEARCH (Google API Implementation) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    # Strategy: Search for the domain + keywords for decision makers
    query = f'"{request.domain}" "email" (CEO OR Founder OR Owner)'
    
    api_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 5  # Fetch top 5 results (Save quota)
    }

    try:
        response = requests.get(api_url, params=params)
        data = response.json()

        # Handle API Errors (e.g., Quota exceeded)
        if "error" in data:
            print("Google API Error:", data["error"])
            return {"status": "error", "message": "Search quota exceeded or API error."}

        found_emails = []
        snippets = []

        # Parse Google Results
        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                
                # Combine text to search for emails
                full_text = f"{title} {snippet}"
                extracted = extract_emails_from_text(full_text)
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