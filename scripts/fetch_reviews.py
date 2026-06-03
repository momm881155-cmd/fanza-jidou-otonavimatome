import json
import time
from typing import Any

import requests

GRAPHQL_URL = "https://api.video.dmm.co.jp/graphql"

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


def fetch_reviews(content_id: str) -> list[dict[str, Any]]:
    """
    指定作品のレビューを取得
    """

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
    with open(
        "data/selected_candidates.json",
        "r",
        encoding="utf-8",
    ) as f:
        works = json.load(f)

    reviews_db: dict[str, list[dict[str, Any]]] = {}

    for work in works:
        content_id = work.get("content_id")

        if not content_id:
            continue

        print(f"[REVIEW] {content_id}")

        try:
            reviews = fetch_reviews(content_id)
            reviews_db[content_id] = reviews

            print(f"  -> {len(reviews)} reviews")

        except Exception as e:
            print(f"  -> ERROR: {e}")
            reviews_db[content_id] = []

        time.sleep(0.5)

    with open(
        "data/reviews.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            reviews_db,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nsaved reviews={len(reviews_db)}")


if __name__ == "__main__":
    main()
