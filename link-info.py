import requests
import json
import sys
from hoarder import get_arg_and_icon, format_title_without_tags, HOARDER_SERVER_ADDR, HEADERS


def generate_mods(bookmark):
    """
    Generate modifiers for Alfred Script Filter JSON output
    For general items excet for "Go Back", Note, Tags and title entry.
    """
    mods = {
        "cmd": {
            "arg": get_arg_and_icon(bookmark)[0],
        },
        "option": {
            "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark['id']}",
        },
        "shift": {
            "arg": f"[{format_title_without_tags(bookmark)}]({get_arg_and_icon(bookmark)[0]})",
        },
    }
    return mods

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
                    "title": "Error fetching bookmark details - Go Back",
                    "subtitle": str(e),
                    "icon": {"path": "icons/goback.png"},
                    "arg": ":action:back"
                }
            ]
        }))
        sys.exit(1)

def format_alfred_output(bookmark):
    """Format Alfred Script Filter JSON output"""
    items = []

    # Content title and URL (title and subtitle)
    items.append({
        "title": format_title_without_tags(bookmark),
        "subtitle": (bookmark.get("content", {}).get("url", "") or 
                    bookmark.get("content", {}).get("text", "") or 
                    bookmark.get("content", {}).get("fileName", "")),
        "arg": bookmark.get("content", {}).get("url", "") or f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}",
        "mods": {
            "ctrl": {
                "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}",
                ## THOUGHTS: I was thinking alfred textview to edit the title/text/note/summary, sticking with url for now
                #"arg": bookmark.get("content", {}).get("text", "") if bookmark.get("content", {}).get("type") == "text" else f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}"
            },
            "option": {
                "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}"
            },
            "cmd": {
                "arg": bookmark.get("content", {}).get("url", "") or f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark.get('id', '')}",
            },
            "shift": {
                "arg": f"[{format_title_without_tags(bookmark)}]({get_arg_and_icon(bookmark)[0]})"},
            },
        "icon": {
            "path": get_arg_and_icon(bookmark)[1]
        },
        "quicklookurl": bookmark.get("content", {}).get("url")
    })

    tags = ", ".join(tag["name"] for tag in bookmark.get("tags", []))

    # Content description as title and tags as subtitle
    content_description = bookmark["content"].get("description") or "No Description"
    items.append({
        "subtitle": content_description,
        "title": tags if tags else "No Tags",
        #"arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark['id']}",
        "arg": f"tags:{bookmark['id']}", # For calling show_bookmark_tags
        "mods": {
            "cmd": {
                # list all tags
                "arg": tags if tags else "No Tags",
                "subtitle": "Copy tags to clipboard",
            }, 
            "option": {
                "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark['id']}",
            },
            "shift": {
                "arg": f"[{format_title_without_tags(bookmark)}]({get_arg_and_icon(bookmark)[0]})",
            },
        },
        "icon": {"path": "icons/label.png"}
    })

    # Note and summary (if any)
    note = bookmark.get("note", "No Note")
    summary = bookmark.get("summary", "No Summary")
    if note or summary:
        items.append({
            "title": "📝: " + note if note else "📝: No Note",
            "subtitle": "🤖: " + summary if summary else "🤖: No Summary",
            #"arg": bookmark.get("id", "") + "?note=" + note if note else bookmark.get("id", "") + "?summary=" + summary,
            # Format arg as Markdown shown both note and summary if exists
            ## SAME AS ABOVE
            "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark['id']}",
            "mods": {
                "cmd": {
                    "arg": f"Note: {note}" if note else "Summary: {summary}" if summary else "",
                    "subtitle": "Copy note or summary to clipboard",
                },
                "option": {
                    "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark['id']}",
                },
                "shift": {
                    "arg": f"[{format_title_without_tags(bookmark)}]({get_arg_and_icon(bookmark)[0]})",
                },
            },
            "icon": {"path": "icons/ledger.png"}
        })

    # Archived
    items.append({
        "title": "Archived" if bookmark.get("archived", False) else "Not Archived",
        "arg": f"archive:{bookmark['id']}",
        "mods": generate_mods(bookmark),
        "icon": {"path": "icons/white_check_mark.png"} if bookmark.get("archived", False) else {"path": "icons/radio_button.png"}
    })

    # Favorited
    items.append({
        "title": "Favorited" if bookmark.get("favourited", False) else "Not Favorited",
        "arg": f"favorite:{bookmark['id']}",
        "mods": generate_mods(bookmark),
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
        "arg": f"{HOARDER_SERVER_ADDR}/dashboard/preview/{bookmark['id']}",
        "mods": generate_mods(bookmark),
        "icon": {"path": "icons/package.png"}
    })

    # Delete action
    items.append({
        "title": "Delete " + bookmark['content']['type'] + ": " + format_title_without_tags(bookmark),
        "subtitle": bookmark['content']['url'] if bookmark['content']['type'] == "link" else format_title_without_tags(bookmark),
        "arg": f"delete:{bookmark['id']}",
        "mods": generate_mods(bookmark),
        "icon": {"path": "icons/wastebasket.png"}
    })
    # Go back
    items.append({
        "title": "Go Back",
        "arg": ":action:back",
        "mods": {
            "cmd": {
                "arg": ":action:back",
                "subtitle": "Go Back to Search Bookmarks",
            },
            "option": {
                "arg": ":action:back",
                "subtitle": "Go Back to Search Bookmarks",
            },
            "shift": {
                "arg": ":action:back",
                "subtitle": "Go Back to Search Bookmarks",
            },
        },
        "icon": {"path": "icons/goback.png"}
    })

    return json.dumps({"items": items}, indent=2)

def show_bookmark_tags(bookmark):
    """Format bookmark tags as Alfred Script Filter JSON output"""
    items = []
    
    for tag in bookmark.get("tags", []):
        # Add emoji indicator for tag source
        source_indicator = "🤖" if tag.get("attachedBy") == "ai" else "👤"
        
        items.append({
            "title": f"#{tag['name']}",
            "subtitle": f"{source_indicator} • Added by: {tag['attachedBy']}",
            "arg": f"{tag['name']}", # For future tag view
            "icon": {"path": "icons/label.png"},
        })
    
    if not items:
        items.append({
            "title": "No tags found",
            "subtitle": "This bookmark has no tags",
            "arg": "",
            "icon": {"path": "icons/label.png"}
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
    
    # Check if --tags option is provided
    # Check if bookmark is empty
    if bookmark_id == "":
        output = json.dumps({"items": [{"title": "Go Back to Search Bookmarks", "icon": {"path": "icons/goback.png"}, "arg": ":action:back"}]})
    elif len(sys.argv) > 2 and sys.argv[2] == "--tags":
        output = show_bookmark_tags(bookmark)
    else:
        output = format_alfred_output(bookmark)
    
    print(output)
