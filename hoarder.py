import requests
import json
import sys
import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse, quote

# cache at current directory
CACHE_DIR = Path(__file__).parent / "cache"
HOARDER_SERVER_ADDR = os.getenv("HOARDER_SERVER_ADDR")
HORADER_API_URL = f"{HOARDER_SERVER_ADDR}/api/v1/bookmarks"
HOARDER_SEARCH_API_URL = f"{HOARDER_SERVER_ADDR}/api/trpc/bookmarks.searchBookmarks"
HOARDER_API_KEY = os.getenv("HOARDER_API_KEY")
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {HOARDER_API_KEY}"
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
            'limit': 20,  # or larger number
            'page': 1      # or use offset: 0
        }

        ensure_cache_dir()
        
        response = requests.get(HORADER_API_URL, headers=HEADERS, params=params)
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
                    "arg": bookmark.get("url"),
                    "mods": {
                        "cmd": {
                            "arg": bookmark.get("id")
                        }
                    },
                    "icon": {
                        #"path": get_favicon_path(bookmark.get("content", {}).get("favicon"))
                        "path": "icon.png"
                    },
                    "quicklookurl": bookmark.get("content", {}).get("url"),
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
                        "path": "icon.png"
                    }
                }
            ]
        }))
        sys.exit(1)

def search_bookmarks(query=""):
    try:
        ensure_cache_dir()
        
        # Construct the search payload
        search_input = {
            "0": {
                "json": {
                    "text": query
                }
            }
        }
        
        # URL encode the JSON payload
        encoded_input = quote(json.dumps(search_input))
        search_url = f"{HOARDER_SEARCH_API_URL}?batch=1&input={encoded_input}"
        
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        # Extract bookmarks from the search response
        bookmarks = data[0]["result"]["data"]["json"]["bookmarks"] if data else []
        
        # Format bookmarks for Alfred feedback
        alfred_feedback = {
            "items": [
                {
                    "title": (bookmark.get("content", {}).get("title") or 
                             bookmark.get("title") or 
                             "Untitled"),
                    # Show the URL in the subtitle
                    "subtitle": bookmark.get("content", {}).get("url", ""),
                    "arg": bookmark.get("url"),
                    "mods": {
                        "cmd": {
                            "arg": bookmark.get("id")
                        }
                    },
                    "icon": {
                        #"path": get_favicon_path(bookmark.get("content", {}).get("favicon"))
                        "path": "icon.png"
                    },
                    "quicklookurl": bookmark.get("content", {}).get("url"),
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
                    "title": "Error searching bookmarks",
                    "subtitle": str(e),
                    "icon": {
                        "path": "icon.png"
                    }
                }
            ]
        }))
        sys.exit(1)

if __name__ == "__main__":
    # Get search query from command line argument if provided
    #fetch_bookmarks()
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        fetch_bookmarks()
        sys.exit(0)
    search_bookmarks(query)
