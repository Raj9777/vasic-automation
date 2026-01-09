# --- 2. DEEP SEARCH (Google API Implementation) ---
@app.post("/deep-search")
def deep_search(request: DomainRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        raise HTTPException(status_code=500, detail="Server config error: Missing Google API Keys")

    # STRATEGY UPDATE: 
    # 1. We force the "@domain.com" pattern to appear.
    # 2. We look at LinkedIn profiles (where people often put emails in bios).
    query = f'site:linkedin.com/in/ OR site:{request.domain} "{request.domain}" "email" "@ {request.domain}" (CEO OR Founder)'
    
    api_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 10  # INCREASED: Check top 10 results (Cost is same per query usually)
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
                
                # Combine text to search for emails
                full_text = f"{title} {snippet}"
                
                # IMPROVED REGEX: Case insensitive
                extracted = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text, re.IGNORECASE)
                
                # Filter: Only keep emails matching the target domain (High Quality)
                # Remove this if you want ALL emails (even gmail/yahoo)
                valid_emails = [e for e in extracted if request.domain in e.lower()]
                
                found_emails.extend(valid_emails)
                snippets.append({"title": title, "link": link})

        return {
            "status": "success",
            "source": "Google Deep Search",
            "emails": list(set(found_emails)), # Remove duplicates
            "related_links": snippets
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}