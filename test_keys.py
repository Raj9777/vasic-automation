import requests

# --- PASTE YOUR KEYS INSIDE THE QUOTES BELOW ---
API_KEY = "AIzaSyAaQ2mK68zt2QNI7F4dS-EW8fGktuA42mQ" 
CX_ID = "76ec621f00b5d4ebf"
# -----------------------------------------------

def test_google_search():
    print(f"Testing Key: {API_KEY[:5]}... | CX: {CX_ID[:5]}...")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX_ID,
        "q": "Tesla",
        "num": 1
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if "error" in data:
            print("\n❌ FAILED!")
            print("Error Code:", data["error"]["code"])
            print("Message:", data["error"]["message"])
        else:
            print("\n✅ SUCCESS!")
            print("Found:", data["items"][0]["title"])
            print("Your keys are valid!")

    except Exception as e:
        print("Python Error:", e)

if __name__ == "__main__":
    test_google_search()