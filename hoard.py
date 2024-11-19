import requests
import json
import sys
import os

HOARDER_SERVER_ADDR = os.getenv("HOARDER_SERVER_ADDR")
HOARDER_API_URL = f"{HOARDER_SERVER_ADDR}/api/v1/bookmarks"
HOARDER_API_KEY = os.getenv("HOARDER_API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {HOARDER_API_KEY}"
}

def add_bookmark(url):
    """Add a new bookmark to Hoarder"""
    payload = {
        "type": "link",
        "url": url,
        "title": None,
        "archived": False,
        "favourited": False,
        "note": "",
        "summary": "",
        "tags": []
    }

    try:
        response = requests.post(HOARDER_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        bookmark_id = data.get("id", "Unknown ID")
        return f"Successfully added bookmark with ID: {bookmark_id}"
    except requests.exceptions.RequestException as e:
        error_detail = ""
        if hasattr(e.response, 'text'):
            try:
                error_detail = f" - Details: {json.loads(e.response.text)}"
            except json.JSONDecodeError:
                error_detail = f" - Response: {e.response.text}"
        
        print(f"Debug Info:")
        print(f"URL: {HOARDER_API_URL}")
        print(f"Headers: {HEADERS}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        return f"Error adding bookmark: {e}{error_detail}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No link provided.")
        sys.exit(1)

    link = sys.argv[1]
    result = add_bookmark(link)
    print(result)
