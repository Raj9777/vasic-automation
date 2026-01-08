from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str

class EmailResult(BaseModel):
    email: str
    source: str
    confidence: str

class ScrapeResponse(BaseModel):
    leads: List[EmailResult]
    status: str

@app.get("/")
def read_root():
    return {"message": "Vasic Automation Engine is Running 🚀"}

# --- ORIGINAL SCRAPER (FAST) ---
@app.post("/scrape", response_model=ScrapeResponse)
def scrape_emails(request: ScrapeRequest):
    url = request.url
    if not url.startswith("http"):
        url = "https://" + url
    
    # ... (Keep existing scraper logic if you want, or I can paste full file) ...
    # For brevity, I'll paste the full combined file below to ensure no errors.
    
    print(f"🔍 Fast Scrape: {url}")
    found_leads = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        content = response.text
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        raw_emails = set(re.findall(email_pattern, content))
        
        for email in raw_emails:
            if any(x in email for x in ['.png', '.jpg', 'wix', 'sentry', 'example']): continue
            
            confidence = "Generic"
            if any(r in email.lower() for r in ['ceo', 'founder', 'owner']): confidence = "🔥 HIGH VALUE"
            elif any(r in email.lower() for r in ['info', 'contact']): confidence = "Team Inbox"
            else: confidence = "Employee"
                
            found_leads.append({"email": email, "source": "Website Direct", "confidence": confidence})
            
    except Exception:
        pass

    found_leads.sort(key=lambda x: 0 if "HIGH" in x['confidence'] else 1)
    return {"leads": found_leads, "status": "success" if found_leads else "no_leads"}


# --- NEW DEEP SEARCH (INTELLIGENT) ---
@app.post("/deep-search", response_model=ScrapeResponse)
def deep_search(request: ScrapeRequest):
    company_url = request.url
    # Extract clean domain (e.g., "tesla.com" from "https://www.tesla.com")
    domain = company_url.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
    company_name = domain.split('.')[0] # Rough guess of name
    
    print(f"🕵️ Deep Search for: {company_name} ({domain})")
    
    found_leads = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Google Dorks to find emails
    # 1. Search for "CEO email" directly
    # 2. Search LinkedIn profiles with email in bio
    queries = [
        f'site:linkedin.com/in/ "{company_name}" "email" "gmail.com"',
        f'"{domain}" "email" "contact" filetype:pdf',
        f'site:rocketreach.co "{company_name}"',
        f'site:{domain} "email" "contact"'
    ]
    
    for query in queries:
        try:
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            res = requests.get(google_url, headers=headers, timeout=5)
            
            # Extract emails from search results description
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            new_emails = set(re.findall(email_pattern, res.text))
            
            for email in new_emails:
                if any(x in email for x in ['google', 'rating', 'search', 'png', 'jpg']): continue
                
                # Check if it matches company domain OR is a personal executive email
                if domain in email or "gmail.com" in email:
                    confidence = "🌍 Deep Web Found"
                    if "gmail" in email: confidence = "Personal (Likely Executive)"
                    
                    found_leads.append({
                        "email": email,
                        "source": "Google Intelligence",
                        "confidence": confidence
                    })
        except:
            continue
            
    # Remove duplicates
    unique_leads = []
    seen = set()
    for lead in found_leads:
        if lead['email'] not in seen:
            unique_leads.append(lead)
            seen.add(lead['email'])

    return {"leads": unique_leads, "status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
