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
TAGS_SHOWN_COUNT = int(os.getenv("TAGS_SHOWN_COUNT", "0"))

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
    
    return "icon.png"
    # download favicon
    #try:
    #    response = requests.get(favicon_url, timeout=5)
    #    response.raise_for_status()
    #    with open(cache_path, 'wb') as f:
    #        f.write(response.content)
    #    return str(cache_path)
    #except Exception as e:
    #    print(f"Error downloading favicon: {e}", file=sys.stderr)
    #    return "icon.png"

def get_thumbnail_path(asset_id):
    """Download and cache thumbnail for image assets"""
    if not asset_id:
        return "icon.png"
    
    cache_path = CACHE_DIR / f"thumb_{asset_id}.png"
    
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return str(cache_path)
    
    return "icon.png"
    #try:
    #    thumbnail_url = f"{HOARDER_SERVER_ADDR}/api/assets/{asset_id}"
    #    response = requests.get(thumbnail_url, headers=HEADERS, timeout=5)
    #    response.raise_for_status()
    #    with open(cache_path, 'wb') as f:
    #        f.write(response.content)
    #    return str(cache_path)
    #except Exception as e:
    #    print(f"Error downloading thumbnail: {e}", file=sys.stderr)
    #    return "icon.png"

def format_title_with_tags(bookmark):
    """Format title with tags based on TAGS_SHOWN_COUNT"""
    content = bookmark.get("content", {})
    content_type = content.get("type")
    
    if content_type == "asset" and content.get("assetType") == "image":
        title = content.get("fileName", "Untitled Image")
    else:
        title = (bookmark.get("content", {}).get("title") or 
                bookmark.get("title") or 
                "Untitled")
    
    if TAGS_SHOWN_COUNT > 0:
        tags = bookmark.get("tags", [])
        if tags:
            shown_tags = tags[:TAGS_SHOWN_COUNT]
            tags_string = " " + ", ".join(f"#{tag.get('name', '')}" for tag in shown_tags if tag.get('name'))
            title = f"{title}{tags_string}"
    
    return title

def get_arg_and_icon(bookmark):
    """Get appropriate arg and icon path based on content type"""
    content = bookmark.get("content", {})
    content_type = content.get("type")
    
    if content_type == "text" or content_type == "asset":
        #arg = bookmark.get("id", "")
        arg = HOARDER_SERVER_ADDR + "/dashboard/preview/" + bookmark.get("id", "")
        icon_path = ("icon.png" if content_type == "text" else 
                    get_thumbnail_path(content.get("assetId")))
    else:
        arg = content.get("url", "")
        icon_path = get_favicon_path(content.get("favicon"))
    
    return arg, icon_path

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
                    "title": format_title_with_tags(bookmark),
                    "subtitle": (bookmark.get("content", {}).get("url", "") or 
                               bookmark.get("content", {}).get("text", "") or 
                               bookmark.get("content", {}).get("fileName", "")),
                    "arg": get_arg_and_icon(bookmark)[0],
                    "mods": {
                        "cmd": {
                            "arg": bookmark.get("id", "")
                        },
                        "option": {
                            "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}"
                        }
                    },
                    "icon": {
                        "path": get_arg_and_icon(bookmark)[1]
                    },
                    "quicklookurl": bookmark.get("content", {}).get("url"),
                    # create match text, include title, url, description and html content and tags
                    #"match": " ".join(filter(None, [
                    #    bookmark.get("content", {}).get("title", ""),
                    #    bookmark.get("content", {}).get("url", ""),
                    #    bookmark.get("content", {}).get("description", ""),
                    #    bookmark.get("content", {}).get("htmlContent", ""),
                    #    bookmark.get("note", ""),
                    #    bookmark.get("summary", ""),
                    #    # join tags with space
                    #    " ".join(tag.get("name", "") for tag in bookmark.get("tags", []))
                    #])).replace('/', ' ').replace('-', ' ').replace('_', ' ')
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
        
        encoded_input = quote(json.dumps(search_input))
        search_url = f"{HOARDER_SEARCH_API_URL}?batch=1&input={encoded_input}"
        
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        # Extract bookmarks from the search response
        bookmarks = data[0]["result"]["data"]["json"]["bookmarks"] if data else []
        
        # Use the same format as fetch_bookmarks
        alfred_feedback = {
            "items": [
                {
                    "title": format_title_with_tags(bookmark),
                    "subtitle": (bookmark.get("content", {}).get("url", "") or 
                               bookmark.get("content", {}).get("text", "") or 
                               bookmark.get("content", {}).get("fileName", "")),
                    "arg": get_arg_and_icon(bookmark)[0],
                    "mods": {
                        "cmd": {
                            "arg": bookmark.get("id", "")
                        },
                        "option": {
                            "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}"
                        },
                    },
                    "icon": {
                        "path": get_arg_and_icon(bookmark)[1]
                    },
                    "quicklookurl": bookmark.get("content", {}).get("url")
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
