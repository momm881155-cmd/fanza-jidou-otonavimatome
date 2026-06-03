import json
import time
from typing import Any

import requests

GRAPHQL_URL = "https://api.video.dmm.co.jp/graphql"

SELECTED_WORKS_PATH = "data/selected_article_works.json"
REVIEWS_PATH = "data/reviews.json"

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
query UserReviews($id: ID!, $sort: ReviewSort!, $offset: Int!) {
  reviews(contentId: $id, sort: $sort, limit: 10, offset: $offset) {
    items {
      id
      title
      rating
      nickname
      comment
      helpfulCount
      publishDate
    }
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


def fetch_reviews(content_id: str) -> list[dict[str, Any]]:
    payload = {
        "operationName": "UserReviews",
        "query": QUERY,
        "variables": {
            "id": content_id,
            "offset": 0,
            "sort": "RELEASE_DESC",
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

    return (
        data.get("data", {})
        .get("reviews", {})
        .get("items", [])
    )


def main() -> None:
    selected_works = load_json(SELECTED_WORKS_PATH, default=[])

    reviews_db: dict[str, list[dict[str, Any]]] = {}

    fetched = 0
    failed = 0
    skipped = 0

    for work in selected_works:
        content_id = work.get("content_id")

        if not content_id:
            skipped += 1
            continue

        print(f"[REVIEW] {content_id}")

        try:
            reviews = fetch_reviews(content_id)
            reviews_db[content_id] = reviews
            fetched += 1

            print(f"  -> count={len(reviews)}")

        except Exception as e:
            failed += 1
            reviews_db[content_id] = []

            print(f"  -> ERROR: {type(e).__name__}")

        time.sleep(SLEEP_SECONDS)

    save_json(REVIEWS_PATH, reviews_db)

    print("")
    print(f"selected={len(selected_works)}")
    print(f"fetched={fetched}")
    print(f"failed={failed}")
    print(f"skipped={skipped}")
    print(f"saved_reviews={len(reviews_db)}")


if __name__ == "__main__":
    main()
