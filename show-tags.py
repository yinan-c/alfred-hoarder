import requests
import json
import sys
from hoarder import HOARDER_SERVER_ADDR, HEADERS

HOARDER_TAGS_API_URL = f"{HOARDER_SERVER_ADDR}/api/v1/tags"

def fetch_tags():
    try:
        response = requests.get(HOARDER_TAGS_API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        tags = data.get("tags", [])
        
        # Sort tags by number of bookmarks (descending)
        tags.sort(key=lambda x: x.get("numBookmarks", 0), reverse=True)
        
        # Format tags for Alfred feedback
        alfred_feedback = {
            "items": [
                {
                    "title": tag.get("name", "Unnamed Tag"),
                    "subtitle": f"{tag.get('numBookmarks', 0)} bookmark{'s' if tag.get('numBookmarks', 0) != 1 else ''}",
                    "arg": tag.get("name", ""),
                    "icon": {
                        "path": "icon.png"
                    },
                    "variables": {
                        "tag_id": tag.get("id", ""),
                        "tag_name": tag.get("name", "")
                    }
                } for tag in tags
            ]
        }
        
        print(json.dumps(alfred_feedback))

    except requests.exceptions.RequestException as e:
        print(json.dumps({
            "items": [
                {
                    "title": "Error fetching tags",
                    "subtitle": str(e),
                    "icon": {
                        "path": "icon.png"
                    }
                }
            ]
        }))
        sys.exit(1)

if __name__ == "__main__":
    fetch_tags()