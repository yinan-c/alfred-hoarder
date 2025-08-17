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
        items = []
        for tag in tags:
            # Determine who added the tag based on numBookmarksByAttachedType
            attached_by_type = tag.get('numBookmarksByAttachedType', {})
            ai_count = attached_by_type.get('ai', 0)
            human_count = attached_by_type.get('human', 0)
            
            # Determine primary source and format subtitle
            if ai_count > 0 and human_count > 0:
                source_indicator = "🤖👤"
                attached_by = f"ai ({ai_count}) & human ({human_count})"
            elif ai_count > 0:
                source_indicator = "🤖"
                attached_by = "ai"
            elif human_count > 0:
                source_indicator = "👤"
                attached_by = "human"
            else:
                source_indicator = "❓"
                attached_by = "unknown"
            
            items.append({
                "title": f"#{tag.get('name', 'Unnamed Tag')}",
                "subtitle": f"{source_indicator} • {tag.get('numBookmarks', 0)} bookmark{'s' if tag.get('numBookmarks', 0) != 1 else ''} • Added by: {attached_by}",
                "arg": tag.get("name", ""),
                "icon": {
                    "path": "icons/label.png"
                },
                "variables": {
                    "tag_id": tag.get("id", ""),
                    "tag_name": tag.get("name", "")
                }
            })
        
        alfred_feedback = {
            "items": items
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