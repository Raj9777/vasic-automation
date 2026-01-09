import os
import requests
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

# --- APP INITIALIZATION ---
app = FastAPI()

# Enable CORS (Allows your Next.js frontend to talk to this Python backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you can restrict this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# Load keys from Environment Variables (Set these in Render Dashboard)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# Data Model for the Request
class DomainRequest(BaseModel):
    domain: str

# Helper: Regex to find emails in any text
def extract_emails_from_text(text):
    # This pattern finds standard emails (e.g., name@company.com)
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text, re.IGNORECASE)))

# --- 1. FAST SCAN (Scrapes the Website directly) ---
@app.post("/scan-website")
def scan_website(request: DomainRequest):
    # Ensure URL has schema
    url = f"https://{request.domain}" if not request.domain.startswith("http") else request.domain
    
    try:
        # 1. Try to get the website HTML
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 2. Extract text and find emails
        page_text = soup.get_text()
        emails = extract_emails_from_text(page_text)
        
        return {
            "status": "success",
            "source": "Website Scan",
            "emails": emails[:10],  # Return top 10
            "meta_title": soup.title.string if soup.title else "No Title Found"
        }
    except Exception as e:
        return {"status": "error", "message": f"Website scan failed: {str(e)}"}

# --- 2. DEEP SEARCH (Google Custom Search API) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    # Safety Check: Are keys present?
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    # STRATEGY: BROAD SEARCH
    # We search for the domain + keywords that usually appear near emails.
    query = f'"{request.domain}" (email OR "contact" OR "mail to") (CEO OR Founder OR Owner OR Director)'
    
    api_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 10  # Max results per page (efficient use of quota)
    }

    try:
        # 1. Call Google API
        response = requests.get(api_url, params=params)
        data = response.json()

        # 2. Check for Google Errors (Quota etc.)
        if "error" in data:
            print("Google API Error:", data["error"])
            return {"status": "error", "message": "Search quota exceeded or API error."}

        found_emails = []
        snippets = []

        # 3. Parse Results
        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                
                # Combine title and snippet to search for emails
                full_text = f"{title} {snippet}"
                
                # Extract ALL emails found in the text
                extracted = extract_emails_from_text(full_text)
                
                # CLEANUP: Filter out obvious junk
                clean_emails = []
                for email in extracted:
                    email_lower = email.lower()
                    # Filter out common garbage emails
                    if "noreply" not in email_lower and "example.com" not in email_lower:
                        clean_emails.append(email)
                
                found_emails.extend(clean_emails)
                snippets.append({"title": title, "link": link})

        return {
            "status": "success",
            "source": "Google Deep Search",
            "emails": list(set(found_emails)), # Remove duplicates
            "related_links": snippets
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}