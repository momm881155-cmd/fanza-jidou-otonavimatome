import json
import math

with open("data/selected_candidates.json", "r", encoding="utf-8") as f:
    works = json.load(f)

with open("data/extra.json", "r", encoding="utf-8") as f:
    extras = json.load(f)

scored = []

for work in works:
    content_id = work.get("content_id")
    raw = work.get("raw", {})

    review = raw.get("review", {})
    review_count = int(review.get("count") or 0)
    review_average = float(review.get("average") or 0)

    extra = extras.get(content_id, {})
    favorite_count = int(extra.get("favorite_count") or 0)
    weekly_rank = extra.get("weekly_rank")

    rating_score = review_average * 10
    review_score = min(math.log1p(review_count) * 10, 30)
    favorite_score = min(math.log1p(favorite_count) * 5, 40)

    if weekly_rank:
        weekly_score = max(0, 30 - int(weekly_rank) * 0.3)
    else:
        weekly_score = 0

    total_score = (
        rating_score
        + review_score
        + favorite_score
        + weekly_score
    )

    scored.append({
        "content_id": content_id,
        "title": work.get("title"),
        "score": round(total_score, 2),
        "review_average": review_average,
        "review_count": review_count,
        "favorite_count": favorite_count,
        "weekly_rank": weekly_rank,
        "url": work.get("url"),
        "image": work.get("image")
    })

scored.sort(key=lambda x: x["score"], reverse=True)

with open("data/scored_works.json", "w", encoding="utf-8") as f:
    json.dump(scored, f, ensure_ascii=False, indent=2)

print(f"scored={len(scored)}")
