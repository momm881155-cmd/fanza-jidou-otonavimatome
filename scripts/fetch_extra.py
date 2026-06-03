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
query ContentPageData(
  $id: ID!,
  $isLoggedIn: Boolean!,
  $isAmateur: Boolean!,
  $isAnime: Boolean!,
  $isAv: Boolean!,
  $isCinema: Boolean!,
  $isSP: Boolean!,
  $pattern: ShelfGenreCurationPattern!,
  $shouldFetchCuratedGenreIdsForShelf: Boolean!,
  $shouldFetchRelatedTags: Boolean!,
  $shouldGetBookmark: Boolean!,
  $shouldGetLegacyBookmark: Boolean!
) {
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

extras = {}

for work in works[:10]:  # 最初は10件だけ
    content_id = work["content_id"]

    payload = {
        "operationName": "ContentPageData",
        "query": QUERY,
        "variables": {
            "id": content_id,
            "isAmateur": False,
            "isAnime": False,
            "isAv": True,
            "isCinema": False,
            "isLoggedIn": False,
            "isSP": True,
            "pattern": "NICHE",
            "shouldFetchCuratedGenreIdsForShelf": False,
            "shouldFetchRelatedTags": False,
            "shouldGetBookmark": False,
            "shouldGetLegacyBookmark": False
        }
    }

    try:
        r = requests.post(
            GRAPHQL_URL,
            json=payload,
            headers=HEADERS,
            timeout=30
        )

        data = r.json()

        content = (
            data.get("data", {})
            .get("ppvContent", {})
        )

        extras[content_id] = {
            "description": content.get("description"),
            "favorite_count": content.get("wishlistCount"),
            "weekly_rank": content.get("weeklyRanking"),
            "monthly_rank": content.get("monthlyRanking")
        }

        print(content_id)

    except Exception as e:
        print(content_id, e)

with open(
    "data/extra.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        extras,
        f,
        ensure_ascii=False,
        indent=2
    )
