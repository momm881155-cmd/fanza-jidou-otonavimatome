import json
import requests

GRAPHQL_URL = "https://api.video.dmm.co.jp/graphql"

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://video.dmm.co.jp",
    "referer": "https://video.dmm.co.jp/",
    "fanza-device": "BROWSER_MOBILE_ANDROID",
    "user-agent": "Mozilla/5.0"
}

QUERY = """
query ContentPageData($id: ID!) {
  ppvContent(id: $id) {
    id
    description
    wishlistCount
    weeklyRanking: ranking(term: Weekly)
    monthlyRanking: ranking(term: Monthly)
  }
}
"""

with open("data/works.json", "r", encoding="utf-8") as f:
    works = json.load(f)

print(f"works count: {len(works)}")

extras = {}

for work in works[:10]:
    content_id = work.get("content_id")
    print(f"fetch extra: {content_id}")

    payload = {
        "operationName": "ContentPageData",
        "query": QUERY,
        "variables": {
            "id": content_id
        }
    }

    try:
        r = requests.post(
            GRAPHQL_URL,
            json=payload,
            headers=HEADERS,
            timeout=30
        )

        print(f"status: {r.status_code}")

        data = r.json()

        if "errors" in data:
            print("errors:")
            print(json.dumps(data["errors"], ensure_ascii=False, indent=2))

        content = data.get("data", {}).get("ppvContent")

        if not content:
            print(f"no content: {content_id}")
            continue

        extras[content_id] = {
            "description": content.get("description"),
            "favorite_count": content.get("wishlistCount"),
            "weekly_rank": content.get("weeklyRanking"),
            "monthly_rank": content.get("monthlyRanking")
        }

    except Exception as e:
        print(f"exception: {content_id} {e}")

with open("data/extra.json", "w", encoding="utf-8") as f:
    json.dump(extras, f, ensure_ascii=False, indent=2)

print(f"saved extras: {len(extras)}")
