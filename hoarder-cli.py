import json
import sys
import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import subprocess
import requests

# cache at current directory
CACHE_DIR = Path(__file__).parent / "cache"
HOARDER_SERVER_ADDR = os.getenv("HOARDER_SERVER_ADDR")
HOARDER_API_KEY = os.getenv("HOARDER_API_KEY")

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
        ensure_cache_dir()
        
        hoarder_path = subprocess.run(['which', 'hoarder'], capture_output=True, text=True, check=True).stdout.strip()
        if not hoarder_path:
            print(json.dumps({
                "items": [
                    {
                        "title": "Hoarder CLI not found",
                        "subtitle": "Please install hoarder CLI first: npm install -g @hoarderapp/cli",
                        "icon": {
                            "path": "error_icon.png"
                        }
                    }
                ]
            }))
            sys.exit(1)
        result = subprocess.run([hoarder_path, 'bookmarks', 'list', '--json'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        # Parse JSON output from CLI
        bookmarks = json.loads(result.stdout)
        
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
                    "match": " ".join(filter(None, [
                        bookmark.get("content", {}).get("title", ""),
                        bookmark.get("content", {}).get("url", ""),
                        bookmark.get("content", {}).get("description", ""),
                        bookmark.get("content", {}).get("htmlContent", ""),
                        bookmark.get("note", ""),
                        bookmark.get("summary", ""),
                        # join tags with space (tags are now directly strings in a list)
                        " ".join(bookmark.get("tags", []))
                    ])).replace('/', ' ').replace('-', ' ').replace('_', ' ')
                } for bookmark in bookmarks
            ]
        }
        
        print(json.dumps(alfred_feedback))

    except subprocess.CalledProcessError as e:
        print(json.dumps({
            "items": [
                {
                    "title": "Error running hoarder CLI",
                    "subtitle": f"Error: {e.stderr}",
                    "icon": {
                        "path": "error_icon.png"
                    }
                }
            ]
        }))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "items": [
                {
                    "title": "Error parsing CLI output",
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

