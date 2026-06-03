import json
import os
import time
import requests

API_ID = os.environ["FANZA_API_ID"]
AFFILIATE_ID = os.environ["FANZA_AFFILIATE_ID"]

URL = "https://api.dmm.com/affiliate/v3/ItemList"

all_works = []
seen = set()

for offset in [1, 101, 201]:
    params = {
        "api_id": API_ID,
        "affiliate_id": AFFILIATE_ID,
        "site": "FANZA",
        "service": "digital",
        "floor": "videoa",
        "hits": 100,
        "offset": offset,
        "sort": "rank",
        "keyword": "素人",
        "output": "json"
    }

    response = requests.get(URL, params=params, timeout=30)
    print(response.status_code, "offset", offset)

    data = response.json()
    items = data.get("result", {}).get("items", [])

    for item in items:
        content_id = item.get("content_id")

        if not content_id or content_id in seen:
            continue

        seen.add(content_id)

        work = {
            "content_id": content_id,
            "title": item.get("title"),
            "date": item.get("date"),
            "url": item.get("affiliateURL"),
            "image": item.get("imageURL", {}).get("large"),
            "raw": item
        }

        all_works.append(work)

    time.sleep(1)

with open("data/works.json", "w", encoding="utf-8") as f:
    json.dump(all_works, f, ensure_ascii=False, indent=2)

print(f"{len(all_works)} works saved")
