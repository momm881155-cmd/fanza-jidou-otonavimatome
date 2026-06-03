import json
from itertools import combinations
from typing import Any

MIN_GENRE_COUNT = 10
MIN_THEME_WORKS = 7

THEMES_PATH = "data/themes.json"
GENRE_COUNTS_PATH = "data/genre_counts.json"
CANDIDATES_PATH = "data/selected_candidates.json"
USED_WORKS_PATH = "data/used_works.json"

BASE_GENRE = "素人"

EXCLUDE_GENRES = {
    "ハイビジョン",
    "4K",
    "4時間以上作品",
    "8時間以上作品",
    "16時間以上作品",
    "8KVR",
    "ハイクオリティVR",
    "VR専用",
    "ベスト・総集編",
    "女優ベスト・総集編",
    "セット商品",
    "福袋",
    "AI生成作品",
    "独占配信",
    "単体作品",
    "デジモ",
}

GENRE_ALIASES = {
    "素人": ["素人", "しろうと", "シロウト", "応募素人", "初撮り", "素人娘"],
    "巨乳": ["巨乳", "爆乳"],
    "人妻・主婦": ["人妻・主婦", "人妻", "主婦", "奥様", "既婚者"],
    "ナンパ": ["ナンパ", "街角ナンパ", "素人ナンパ"],
    "初撮り": ["初撮り", "初撮り素人"],
}


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


def get_genres(work: dict[str, Any]) -> list[str]:
    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})

    return [
        g.get("name")
        for g in iteminfo.get("genre", [])
        if g.get("name")
    ]


def has_genre(required_genre: str, genres: list[str]) -> bool:
    aliases = GENRE_ALIASES.get(required_genre, [required_genre])
    return any(alias in genres for alias in aliases)


def get_used_content_ids() -> set[str]:
    used_data = load_json(USED_WORKS_PATH, default={"works": []})
    used_works = used_data.get("works", [])

    return {
        item.get("content_id")
        for item in used_works
        if item.get("content_id")
    }


def is_usable_work(work: dict[str, Any], used_ids: set[str]) -> bool:
    content_id = work.get("content_id")

    if not content_id:
        return False

    if content_id in used_ids:
        return False

    genres = get_genres(work)

    return has_genre(BASE_GENRE, genres)


def count_matching_works(
    works: list[dict[str, Any]],
    required_genres: list[str] | None = None,
    min_review_count: int | None = None,
    min_favorite_count: int | None = None,
    require_weekly_rank: bool = False,
    require_monthly_rank: bool = False,
) -> int:
    required_genres = required_genres or []

    count = 0

    for work in works:
        genres = get_genres(work)

        if not has_genre(BASE_GENRE, genres):
            continue

        if required_genres:
            if not all(has_genre(req, genres) for req in required_genres):
                continue

        review_count = work.get("review_count") or 0
        favorite_count = work.get("favorite_count") or 0
        weekly_rank = work.get("weekly_rank")
        monthly_rank = work.get("monthly_rank")

        if min_review_count is not None and review_count < min_review_count:
            continue

        if min_favorite_count is not None and favorite_count < min_favorite_count:
            continue

        if require_weekly_rank and not weekly_rank:
            continue

        if require_monthly_rank and not monthly_rank:
            continue

        count += 1

    return count


def make_genre_pool(genre_counts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    genre_pool = []

    for item in genre_counts:
        genre = item.get("genre")
        count = item.get("count", 0)

        if not genre:
            continue

        if count < MIN_GENRE_COUNT:
            continue

        if genre in EXCLUDE_GENRES:
            continue

        if genre == BASE_GENRE:
            continue

        genre_pool.append({
            "name": genre,
            "count": count,
        })

    return genre_pool


def add_theme(themes: list[dict[str, Any]], theme: dict[str, Any]) -> None:
    if theme.get("count_hint", 0) < MIN_THEME_WORKS:
        return

    themes.append(theme)


def main() -> None:
    genre_counts = load_json(GENRE_COUNTS_PATH, default=[])
    all_works = load_json(CANDIDATES_PATH, default=[])

    used_ids = get_used_content_ids()

    works = [
        work
        for work in all_works
        if is_usable_work(work, used_ids)
    ]

    genre_pool = make_genre_pool(genre_counts)

    themes: list[dict[str, Any]] = []

    for g in genre_pool:
        genre_name = g["name"]
        count_hint = count_matching_works(
            works,
            required_genres=[genre_name],
        )

        add_theme(themes, {
            "type": "genre",
            "name": f"素人×{genre_name}",
            "base_genre": BASE_GENRE,
            "theme_genre": genre_name,
            "required": [BASE_GENRE, genre_name],
            "sort_key": "score",
            "count_hint": count_hint,
        })

    for g1, g2 in combinations(genre_pool, 2):
        genre_1 = g1["name"]
        genre_2 = g2["name"]

        count_hint = count_matching_works(
            works,
            required_genres=[genre_1, genre_2],
        )

        add_theme(themes, {
            "type": "combo",
            "name": f"素人×{genre_1}×{genre_2}",
            "base_genre": BASE_GENRE,
            "theme_genres": [genre_1, genre_2],
            "theme_genre": genre_1,
            "required": [BASE_GENRE, genre_1, genre_2],
            "sort_key": "score",
            "count_hint": count_hint,
        })

    review_themes = [
        {
            "type": "review_count",
            "name": "レビュー数が多い素人作品10選",
            "base_genre": BASE_GENRE,
            "sort_key": "review_count",
            "min_review_count": 3,
        },
        {
            "type": "review_count",
            "name": "レビュー10件以上の素人作品10選",
            "base_genre": BASE_GENRE,
            "sort_key": "review_count",
            "min_review_count": 10,
        },
    ]

    for theme in review_themes:
        count_hint = count_matching_works(
            works,
            min_review_count=theme["min_review_count"],
        )
        theme["count_hint"] = count_hint
        add_theme(themes, theme)

    for g in genre_pool:
        genre_name = g["name"]

        count_hint = count_matching_works(
            works,
            required_genres=[genre_name],
            min_review_count=3,
        )

        add_theme(themes, {
            "type": "review_count_genre",
            "name": f"レビュー数が多い素人×{genre_name}作品10選",
            "base_genre": BASE_GENRE,
            "theme_genre": genre_name,
            "required": [BASE_GENRE, genre_name],
            "sort_key": "review_count",
            "min_review_count": 3,
            "count_hint": count_hint,
        })

    popularity_themes = [
        {
            "type": "favorite_count",
            "name": "お気に入り数が多い素人作品10選",
            "base_genre": BASE_GENRE,
            "sort_key": "favorite_count",
            "min_favorite_count": 100,
        },
        {
            "type": "ranking",
            "name": "週間ランキング入りの素人作品10選",
            "base_genre": BASE_GENRE,
            "sort_key": "weekly_rank",
            "require_weekly_rank": True,
        },
        {
            "type": "ranking",
            "name": "月間ランキング入りの素人作品10選",
            "base_genre": BASE_GENRE,
            "sort_key": "monthly_rank",
            "require_monthly_rank": True,
        },
    ]

    for theme in popularity_themes:
        count_hint = count_matching_works(
            works,
            min_favorite_count=theme.get("min_favorite_count"),
            require_weekly_rank=theme.get("require_weekly_rank", False),
            require_monthly_rank=theme.get("require_monthly_rank", False),
        )
        theme["count_hint"] = count_hint
        add_theme(themes, theme)

    seen = set()
    unique_themes = []

    for theme in themes:
        name = theme.get("name")

        if not name:
            continue

        if name in seen:
            continue

        seen.add(name)
        unique_themes.append(theme)

    unique_themes.sort(
        key=lambda x: (
            x.get("type", ""),
            -x.get("count_hint", 0),
            x.get("name", ""),
        )
    )

    save_json(THEMES_PATH, unique_themes)

    type_counts: dict[str, int] = {}

    for theme in unique_themes:
        theme_type = theme.get("type", "unknown")
        type_counts[theme_type] = type_counts.get(theme_type, 0) + 1

    print(f"works={len(all_works)}")
    print(f"usable_works={len(works)}")
    print(f"themes={len(unique_themes)}")
    print("themes_by_type:")
    print(json.dumps(type_counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
