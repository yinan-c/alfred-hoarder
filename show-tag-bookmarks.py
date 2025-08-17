import requests
import json
import sys
from hoarder import (
    HOARDER_SERVER_ADDR,
    HEADERS,
    ensure_cache_dir,
    get_favicon_path,
    get_thumbnail_path,
    format_title_with_tags,
    format_title_without_tags,
    get_arg_and_icon
)


def get_tag_id_by_name(tag_name):
    """Get tag ID by tag name (case insensitive)"""
    try:
        tags_url = f"{HOARDER_SERVER_ADDR}/api/v1/tags"
        response = requests.get(tags_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        tags = data.get("tags", [])
        for tag in tags:
            if tag.get("name", "").lower() == tag_name.lower():
                return tag.get("id")
        
        return None
    except requests.exceptions.RequestException:
        return None

def fetch_bookmarks_by_tag(tag_name):
    try:
        ensure_cache_dir()
        
        # First get the tag ID from the tag name
        tag_id = get_tag_id_by_name(tag_name)
        
        if not tag_id:
            print(json.dumps({
                "items": [
                    {
                        "title": "Go Back to Tags",
                        "subtitle": "Return to tag list",
                        "icon": {
                            "path": "icons/goback.png"
                        },
                        "arg": ":action:back"
                    },
                    {
                        "title": f"Tag '{tag_name}' not found",
                        "subtitle": "The specified tag does not exist",
                        "icon": {
                            "path": "icon.png"
                        }
                    }
                ]
            }))
            return
        
        # Construct the API URL for fetching bookmarks by tag
        api_url = f"{HOARDER_SERVER_ADDR}/api/v1/tags/{tag_id}/bookmarks"
        
        # Add pagination params
        params = {
            'limit': 50,
            'includeContent': 'true',
            'sortOrder': 'desc'
        }
        
        response = requests.get(api_url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        bookmarks = data.get("bookmarks", [])
        
        # Format bookmarks for Alfred feedback
        items = []
        
        # Add "Go Back" item at the beginning
        items.append({
            "title": "Go Back to Tags",
            "subtitle": "Return to tag list",
            "icon": {
                "path": "icons/goback.png"
            },
            "arg": ":action:back"
        })
        
        # Add bookmark items
        items.extend([
            {
                "title": format_title_with_tags(bookmark),
                    "subtitle": (bookmark.get("content", {}).get("url", "") or 
                               bookmark.get("content", {}).get("text", "") or 
                               bookmark.get("content", {}).get("fileName", "")),
                    "arg": get_arg_and_icon(bookmark)[0],
                    "mods": {
                        "ctrl": {
                            "arg": bookmark.get("id", "")
                        },
                        "cmd": {
                            "arg": get_arg_and_icon(bookmark)[0],
                        },
                        "option": {
                            "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}"
                        },
                        "shift": {
                            "arg": f"[{format_title_without_tags(bookmark)}]({get_arg_and_icon(bookmark)[0]})"
                        }
                    },
                    "icon": {
                        "path": get_arg_and_icon(bookmark)[1]
                    },
                    "quicklookurl": bookmark.get("content", {}).get("url")
                } for bookmark in bookmarks
            ])
        
        # If no bookmarks found, show only Go Back and message
        if not bookmarks:
            items = [{
                "title": "Go Back to Tags",
                "subtitle": "Return to tag list",
                "icon": {
                    "path": "icons/goback.png"
                },
                "arg": ":action:back"
            }, {
                "title": "No bookmarks found",
                "subtitle": "This tag has no associated bookmarks",
                "icon": {
                    "path": "icon.png"
                }
            }]
        
        alfred_feedback = {"items": items}
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

if __name__ == "__main__":
    # Get tag name from command line argument
    if len(sys.argv) < 2:
        print(json.dumps({
            "items": [
                {
                    "title": "Error: No tag name provided",
                    "subtitle": "Please provide a tag name",
                    "icon": {
                        "path": "icon.png"
                    }
                }
            ]
        }))
        sys.exit(1)
    
    tag_name = sys.argv[1]
    fetch_bookmarks_by_tag(tag_name)