import json
import math
from typing import Any

CANDIDATES_PATH = "data/selected_candidates.json"
SCORED_PATH = "data/scored_works.json"


def load_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def get_review_info(work: dict[str, Any]) -> tuple[int, float]:
    raw = work.get("raw", {})
    review = raw.get("review", {})

    review_count = to_int(review.get("count"))
    review_average = to_float(review.get("average"))

    return review_count, review_average


def calculate_score(
    review_count: int,
    review_average: float,
) -> float:
    rating_score = 0
    review_count_score = 0

    if review_count > 0 and review_average > 0:
        rating_score = review_average * 10

    review_count_score = min(math.log1p(review_count) * 12, 40)

    # レビュー件数が少ない高評価の過大評価を防ぐ
    confidence_bonus = 0

    if review_count >= 10:
        confidence_bonus = 15
    elif review_count >= 5:
        confidence_bonus = 8
    elif review_count >= 3:
        confidence_bonus = 4

    total_score = (
        rating_score
        + review_count_score
        + confidence_bonus
    )

    return round(total_score, 2)


def main() -> None:
    works = load_json(CANDIDATES_PATH, default=[])

    scored = []

    for work in works:
        content_id = work.get("content_id")

        if not content_id:
            continue

        review_count, review_average = get_review_info(work)

        score = calculate_score(
            review_count=review_count,
            review_average=review_average,
        )

        scored.append({
            "content_id": content_id,
            "title": work.get("title"),
            "score": score,
            "review_average": review_average,
            "review_count": review_count,
            "url": work.get("url"),
            "image": work.get("image"),
        })

    scored.sort(
        key=lambda x: (
            x.get("score", 0),
            x.get("review_count", 0),
        ),
        reverse=True,
    )

    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=2)

    print(f"scored={len(scored)}")


if __name__ == "__main__":
    main()
