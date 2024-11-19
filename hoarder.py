import requests
import json
import sys
import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse

# cache at current directory
CACHE_DIR = Path(__file__).parent / "cache"
HOST_URL = os.getenv("HOST_URL")
API_URL = f"{HOST_URL}/api/v1/bookmarks"
API_KEY = os.getenv("API_KEY")
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_favicon_path(favicon_url):
    """Download favicon and return local path"""
    if not favicon_url:
        return "icon.png"
    
    # use md5 as file name
    favicon_hash = hashlib.md5(favicon_url.encode()).hexdigest()
    file_extension = Path(urlparse(favicon_url).path).suffix or '.ico'
    cache_path = CACHE_DIR / f"{favicon_hash}{file_extension}"

    # if cache exists and is not empty, return it
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return str(cache_path)
    
    # download favicon
    try:
        response = requests.get(favicon_url, timeout=5)
        response.raise_for_status()
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        return str(cache_path)
    except Exception as e:
        print(f"Error downloading favicon: {e}", file=sys.stderr)
        return "icon.png"

def fetch_bookmarks():
    try:
        # add pagination params
        params = {
            'limit': 100,  # or larger number
            'page': 1      # or use offset: 0
        }

        ensure_cache_dir()
        
        response = requests.get(API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        # print actual data structure
        #print("DEBUG: API Response:", json.dumps(data, indent=2), file=sys.stderr)        
        # print response headers
        #print("DEBUG Headers:", dict(response.headers), file=sys.stderr)
        #print("DEBUG Total bookmarks:", len(data.get("bookmarks", [])), file=sys.stderr)
        
        # DEBUG; get data directly, not use .get("bookmarks")
        #bookmarks = data if isinstance(data, list) else data.get("bookmarks", [])        
        bookmarks = data.get("bookmarks", [])
        
        # Format bookmarks for Alfred feedback
        alfred_feedback = {
            "items": [
                {
                    "title": (bookmark.get("content", {}).get("title") or 
                             bookmark.get("title") or 
                             "Untitled"),
                    "subtitle": bookmark.get("content", {}).get("url", ""),
                    "arg": bookmark.get("id"),
                    "icon": {
                        "path": get_favicon_path(bookmark.get("content", {}).get("favicon"))
                    },
                    # create match text, include title, url, description and html content and tags
                    "match": " ".join(filter(None, [
                        bookmark.get("content", {}).get("title", ""),
                        bookmark.get("content", {}).get("url", ""),
                        bookmark.get("content", {}).get("description", ""),
                        bookmark.get("content", {}).get("htmlContent", ""),
                        bookmark.get("note", ""),
                        bookmark.get("summary", ""),
                        # join tags with space
                        " ".join(tag.get("name", "") for tag in bookmark.get("tags", []))
                    ])).replace('/', ' ').replace('-', ' ').replace('_', ' ')
                } for bookmark in bookmarks
            ]
        }
        
        print(json.dumps(alfred_feedback))

    except requests.exceptions.RequestException as e:
        print(json.dumps({
            "items": [
                {
                    "title": "Error fetching bookmarks",
                    "subtitle": str(e),
                    "icon": {
                        "path": "error_icon.png"
                    }
                }
            ]
        }))
        sys.exit(1)

if __name__ == "__main__":
    fetch_bookmarks()

