import json
import time
from typing import Any

import requests

GRAPHQL_URL = "https://api.video.dmm.co.jp/graphql"

SELECTED_WORKS_PATH = "data/selected_article_works.json"
EXTRA_PATH = "data/extra.json"

SLEEP_SECONDS = 0.5

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://video.dmm.co.jp",
    "referer": "https://video.dmm.co.jp/",
    "fanza-device": "BROWSER_MOBILE_ANDROID",
    "user-agent": "Mozilla/5.0",
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


def load_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_extra(content_id: str) -> dict[str, Any] | None:
    payload = {
        "operationName": "ContentPageData",
        "query": QUERY,
        "variables": {
            "id": content_id,
        },
    }

    response = requests.post(
        GRAPHQL_URL,
        json=payload,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    content = data.get("data", {}).get("ppvContent")

    if not content:
        return None

    return {
        "description": content.get("description"),
        "favorite_count": content.get("wishlistCount"),
        "weekly_rank": content.get("weeklyRanking"),
        "monthly_rank": content.get("monthlyRanking"),
    }


def main() -> None:
    works = load_json(SELECTED_WORKS_PATH, default=[])

    extras: dict[str, dict[str, Any]] = {}

    fetched = 0
    failed = 0
    skipped = 0
    no_content = 0

    for work in works:
        content_id = work.get("content_id")

        if not content_id:
            skipped += 1
            continue

        print(f"[EXTRA] {content_id}")

        try:
            extra = fetch_extra(content_id)

            if not extra:
                no_content += 1
                print("  -> no_content")
                continue

            extras[content_id] = extra
            fetched += 1

            print("  -> ok")

        except Exception as e:
            failed += 1
            print(f"  -> ERROR: {type(e).__name__}")

        time.sleep(SLEEP_SECONDS)

    save_json(EXTRA_PATH, extras)

    print("")
    print(f"selected={len(works)}")
    print(f"fetched={fetched}")
    print(f"failed={failed}")
    print(f"skipped={skipped}")
    print(f"no_content={no_content}")
    print(f"saved_extras={len(extras)}")


if __name__ == "__main__":
    main()
