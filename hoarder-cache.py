import requests
import json
import sys
import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse, quote
from hoarder import CACHE_DIR, HOARDER_SERVER_ADDR, HORADER_API_URL, HOARDER_SEARCH_API_URL, HEADERS
from hoarder import ensure_cache_dir

def download_favicon(favicon_url):
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

def download_thumbnail(asset_id):
    """Download and cache thumbnail for image assets"""
    if not asset_id:
        return "icon.png"
    
    cache_path = CACHE_DIR / f"thumb_{asset_id}.png"
    
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return str(cache_path)
    
    try:
        thumbnail_url = f"{HOARDER_SERVER_ADDR}/api/assets/{asset_id}"
        response = requests.get(thumbnail_url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        return str(cache_path)
    except Exception as e:
        return "icon.png"

def fetch_bookmarks_icon():
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
   
        bookmarks = data.get("bookmarks", [])
        for bookmark in bookmarks:
            download_icon_and_thumbnail(bookmark)

    except requests.exceptions.RequestException as e:
        sys.exit(1)

def download_icon_and_thumbnail(bookmark):
    """Get appropriate arg and icon path based on content type"""
    content = bookmark.get("content", {})
    content_type = content.get("type")
    
    if content_type == "text" or content_type == "asset":
        download_thumbnail(content.get("assetId"))
    else:
        download_favicon(content.get("favicon"))

def search_bookmarks_icon(query=""):
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
        
        encoded_input = quote(json.dumps(search_input))
        search_url = f"{HOARDER_SEARCH_API_URL}?batch=1&input={encoded_input}"
        
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        # Extract bookmarks from the search response
        bookmarks = data[0]["result"]["data"]["json"]["bookmarks"] if data else []
        
        for bookmark in bookmarks:
            download_icon_and_thumbnail(bookmark)

    except requests.exceptions.RequestException as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Get search query from command line argument if provided
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        fetch_bookmarks_icon()
        sys.exit(0)
    search_bookmarks_icon(query)
