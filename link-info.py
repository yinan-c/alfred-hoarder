import requests
import json
import sys
import os
from hoarder import get_arg_and_icon, format_title_with_tags

# Hoarder API configuration
HOARDER_SERVER_ADDR = os.getenv("HOARDER_SERVER_ADDR")
HOARDER_API_KEY = os.getenv("HOARDER_API_KEY")
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {HOARDER_API_KEY}"
}

def get_bookmark_details(bookmark_id):
    """Fetch bookmark details from the Hoarder API"""
    url = f"{HOARDER_SERVER_ADDR}/api/v1/bookmarks/{bookmark_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(json.dumps({
            "items": [
                {
                    "title": "Error fetching bookmark details",
                    "subtitle": str(e),
                    "icon": {"path": "icon.png"}
                }
            ]
        }))
        sys.exit(1)

def format_alfred_output(bookmark):
    """Format Alfred Script Filter JSON output"""
    items = []

    # Content title and URL (title and subtitle)
    items.append({
        "title": format_title_with_tags(bookmark),
        "subtitle": (bookmark.get("content", {}).get("url", "") or 
                    bookmark.get("content", {}).get("text", "") or 
                    bookmark.get("content", {}).get("fileName", "")),
        "arg": get_arg_and_icon(bookmark)[0],
        "mods": {
            "cmd": {
                "arg": HOARDER_SERVER_ADDR + "/dashboard/preview/" + bookmark.get("id", "")
            }
        },
        "icon": {
            "path": get_arg_and_icon(bookmark)[1]
        },
        "quicklookurl": bookmark.get("content", {}).get("url")
    })

    tags = ", ".join(tag["name"] for tag in bookmark.get("tags", []))

    # Content description as title and tags as subtitle
    content_description = bookmark["content"].get("description", "No Description")
    items.append({
        "subtitle": content_description,
        "title": tags if tags else "No Tags",
        "arg": content_description,
        "icon": {"path": "icons/label.png"}
    })

    # Note and summary (if any)
    note = bookmark.get("note", "No Note")
    summary = bookmark.get("summary", "No Summary")
    if note or summary:
        items.append({
            "title": "📝: " + note if note else "📝: No Note",
            "subtitle": "🤖: " + summary if summary else "🤖: No Summary",
            "arg": note or summary,
            "icon": {"path": "icons/ledger.png"}
        })

    # Archived
    items.append({
        "title": "Archived" if bookmark.get("archived", False) else "Not Archived",
        "arg": bookmark.get("archived", False),
        "icon": {"path": "icons/white_check_mark.png"} if bookmark.get("archived", False) else {"path": "icons/radio_button.png"}
    })

    # Favorited
    items.append({
        "title": "Favorited" if bookmark.get("favourited", False) else "Not Favorited",
        "arg": bookmark.get("favourited", False),
        "icon": {"path": "icons/star.png"} if bookmark.get("favourited", False) else {"path": "icons/radio_button.png"}
    })

    # Screenshots or full page archive
    screenshots = any(asset["assetType"] == "screenshot" for asset in bookmark.get("assets", []))
    full_page_archive = any(asset["assetType"] == "fullPageArchive" for asset in bookmark.get("assets", []))

    def get_emoji_for_boolean(boolean):
        if boolean:
            return "✅"
        else:   
            return "🔘"

    items.append({
        "title": "Screenshots: " + get_emoji_for_boolean(screenshots) + " Full Page Archive: " + get_emoji_for_boolean(full_page_archive),
        "arg": get_emoji_for_boolean(screenshots) + " " + get_emoji_for_boolean(full_page_archive),
        "icon": {"path": "icons/package.png"}
    })

    # Delete action
    items.append({
        "title": "Delete Bookmark",
        "subtitle": f"Bookmark ID: {bookmark['id']}",
        "arg": f"delete:{bookmark['id']}",
        "icon": {"path": "icons/wastebasket.png"}
    })

    return json.dumps({"items": items}, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "items": [
                {
                    "title": "Error: No bookmark ID provided",
                    "subtitle": "Usage: python3 link-info.py {id}",
                    "icon": {"path": "icon.png"}
                }
            ]
        }))
        sys.exit(1)

    bookmark_id = sys.argv[1]
    bookmark = get_bookmark_details(bookmark_id)
    alfred_output = format_alfred_output(bookmark)
    print(alfred_output)
