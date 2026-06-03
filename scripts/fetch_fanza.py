import json
import os
import time
from typing import Any

import requests

API_ID = os.environ["FANZA_API_ID"]
AFFILIATE_ID = os.environ["FANZA_AFFILIATE_ID"]

URL = "https://api.dmm.com/affiliate/v3/ItemList"

OUTPUT_PATH = "data/works.json"

KEYWORD = "素人"
HITS = 100
MAX_ITEMS = 1000
SLEEP_SECONDS = 1


def fetch_items(offset: int) -> list[dict[str, Any]]:
    params = {
        "api_id": API_ID,
        "affiliate_id": AFFILIATE_ID,
        "site": "FANZA",
        "service": "digital",
        "floor": "videoa",
        "hits": HITS,
        "offset": offset,
        "sort": "rank",
        "keyword": KEYWORD,
        "output": "json",
    }

    response = requests.get(URL, params=params, timeout=30)
    print(f"status={response.status_code} offset={offset}")

    response.raise_for_status()

    data = response.json()
    return data.get("result", {}).get("items", [])


def normalize_work(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "content_id": item.get("content_id"),
        "title": item.get("title"),
        "date": item.get("date"),
        "url": item.get("affiliateURL"),
        "image": item.get("imageURL", {}).get("large"),
        "raw": item,
    }


def main() -> None:
    all_works = []
    seen = set()

    for offset in range(1, MAX_ITEMS + 1, HITS):
        items = fetch_items(offset)

        if not items:
            print(f"no_items offset={offset}")
            break

        added = 0

        for item in items:
            content_id = item.get("content_id")

            if not content_id:
                continue

            if content_id in seen:
                continue

            seen.add(content_id)
            all_works.append(normalize_work(item))
            added += 1

        print(f"items={len(items)} added={added} total={len(all_works)}")

        if len(items) < HITS:
            print("last_page_detected")
            break

        if len(all_works) >= MAX_ITEMS:
            break

        time.sleep(SLEEP_SECONDS)

    all_works = all_works[:MAX_ITEMS]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)

    print(f"{len(all_works)} works saved")


if __name__ == "__main__":
    main()
