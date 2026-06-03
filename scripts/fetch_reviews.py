import json
import requests

CONTENT_ID = "sqte00659"

url = "https://api.video.dmm.co.jp/graphql"

payload = {
    "operationName": "UserReviews",
    "query": """
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
    """,
    "variables": {
        "id": CONTENT_ID,
        "offset": 0,
        "sort": "RELEASE_DESC"
    }
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://video.dmm.co.jp",
    "referer": "https://video.dmm.co.jp/",
    "fanza-device": "BROWSER_MOBILE_ANDROID",
    "user-agent": "Mozilla/5.0"
}

response = requests.post(
    url,
    json=payload,
    headers=headers,
    timeout=30
)

print(response.status_code)

data = response.json()

with open(
    "data/reviews.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )

print("saved reviews")
