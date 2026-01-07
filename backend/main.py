from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import re
from typing import List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow Frontend to talk to Backend (CORS Fix)
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
async def scrape_emails(request: ScrapeRequest):
    url = request.url
    if not url.startswith("http"):
        url = "https://" + url
        
    print(f"🔍 Starting scrape for: {url}")
    
    found_leads = []
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # 1. Scrape Homepage
                print("   -> Loading Homepage...")
                await page.goto(url, timeout=30000)
                content = await page.content()
                
                # 2. Try to find "About" or "Contact" page
                # This makes us look like a human browsing
                links = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('a')).map(a => a.href)
                """)
                about_pages = [link for link in links if any(x in link.lower() for x in ['about', 'contact', 'team', 'people'])]
                
                # Scrape specific pages if found (limit to first 2 to save time)
                # Remove duplicates and limit
                unique_pages = list(set(about_pages))[:2]
                
                for sub_page in unique_pages:
                    try:
                        print(f"   -> Checking sub-page: {sub_page}")
                        await page.goto(sub_page, timeout=15000)
                        content += await page.content()
                    except:
                        continue

                # 3. Extraction Logic
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                raw_emails = set(re.findall(email_pattern, content))
                
                for email in raw_emails:
                    # Filter junk
                    if any(x in email for x in ['.png', '.jpg', '.gif', 'wix', 'sentry', 'example', 'domain', 'email']):
                        continue
                        
                    # 4. "High Value" Detection
                    confidence = "Generic"
                    lower_email = email.lower()
                    
                    if any(role in lower_email for role in ['ceo', 'founder', 'owner', 'director', 'marketing', 'sales', 'head']):
                        confidence = "🔥 HIGH VALUE (Decision Maker)"
                    elif any(role in lower_email for role in ['info', 'contact', 'support', 'hello', 'admin', 'office']):
                        confidence = "Team Inbox"
                    else:
                        confidence = "Employee (Personal)"
                        
                    found_leads.append({
                        "email": email,
                        "source": "Website Scrape",
                        "confidence": confidence
                    })
                        
            except Exception as e:
                print(f"Error accessing page: {e}")
            finally:
                await browser.close()
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Sort leads: High Value first
    found_leads.sort(key=lambda x: 0 if "HIGH" in x['confidence'] else 1)

    return {
        "leads": found_leads,
        "status": "success" if found_leads else "no_leads_found"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
