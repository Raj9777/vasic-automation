from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
from bs4 import BeautifulSoup
from typing import List
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

@app.post("/scrape", response_model=ScrapeResponse)
def scrape_emails(request: ScrapeRequest):
    url = request.url
    if not url.startswith("http"):
        url = "https://" + url
        
    print(f"🔍 Starting scrape for: {url}")
    found_leads = []
    
    # Fake browser headers to avoid getting blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 1. Scrape Homepage
        response = requests.get(url, headers=headers, timeout=10)
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        
        # 2. Find internal links (Contact, About)
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(x in href.lower() for x in ['about', 'contact', 'team']):
                if href.startswith('http'):
                    links.add(href)
                elif href.startswith('/'):
                    links.add(url.rstrip('/') + href)
        
        # Scrape sub-pages
        for link in list(links)[:2]:
            try:
                print(f"   -> Checking: {link}")
                res = requests.get(link, headers=headers, timeout=5)
                content += res.text
            except:
                continue

        # 3. Extract Emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        raw_emails = set(re.findall(email_pattern, content))
        
        for email in raw_emails:
            # Filter junk
            if any(x in email for x in ['.png', '.jpg', '.gif', 'wix', 'sentry', 'example', 'domain']):
                continue
                
            # 4. Intelligence
            confidence = "Generic"
            lower = email.lower()
            if any(role in lower for role in ['ceo', 'founder', 'owner', 'director', 'marketing']):
                confidence = "🔥 HIGH VALUE"
            elif any(role in lower for role in ['info', 'contact', 'support']):
                confidence = "Team Inbox"
            else:
                confidence = "Employee"
                
            found_leads.append({
                "email": email,
                "source": "Website Scrape",
                "confidence": confidence
            })
            
    except Exception as e:
        print(f"Error: {e}")
        # Don't crash, just return empty list if failed
        pass

    found_leads.sort(key=lambda x: 0 if "HIGH" in x['confidence'] else 1)

    return {
        "leads": found_leads,
        "status": "success" if found_leads else "no_leads_found"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
