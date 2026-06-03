import json
import os
import requests

API_ID = os.environ["FANZA_API_ID"]
AFFILIATE_ID = os.environ["FANZA_AFFILIATE_ID"]

url = "https://api.dmm.com/affiliate/v3/ItemList"

params = {
    "api_id": API_ID,
    "affiliate_id": AFFILIATE_ID,
    "site": "FANZA",
    "service": "digital",
    "floor": "videoa",
    "hits": 10,
    "sort": "rank",
    "keyword": "素人",
    "output": "json"
}

response = requests.get(url, params=params)

print(response.status_code)

data = response.json()

works = []

for item in data.get("result", {}).get("items", []):

    work = {
        "content_id": item.get("content_id"),
        "title": item.get("title"),
        "maker": item.get("maker", {}).get("name"),
        "date": item.get("date"),
        "url": item.get("affiliateURL"),
        "image": item.get("imageURL", {}).get("large")
    }

    works.append(work)

with open("data/works.json", "w", encoding="utf-8") as f:
    json.dump(
        works,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"{len(works)} works saved")
