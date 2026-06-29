import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

TOP_N = 10
MIN_SELECTED = 5

MAX_SERIES = 2
MAX_MAKER = 3
DAYS_LIMIT = 60

WORKS_PATH = "data/selected_article_works.json"

SERIES_PATTERNS = [
    "マジックミラー号",
    "マジックミラー便",
    "一般男女モニタリングAV",
    "素人ナンパGET",
    "タダマンFile",
    "ラグジュTV",
    "街角シロウトナンパ",
    "新・素人娘",
    "初撮り",
    "応募素人",
    "SOD女子社員",
    "MGS動画",
    "シロウトTV",
    "ナンパJAPAN",
]

GENRE_ALIASES = {
    "素人": ["素人", "しろうと", "シロウト", "応募素人", "初撮り", "素人娘"],
    "巨乳": ["巨乳", "爆乳"],
    "人妻・主婦": ["人妻・主婦", "人妻", "主婦", "奥様", "既婚者"],
    "女子大生": ["女子大生", "大学生"],
    "熟女": ["熟女"],
    "ナンパ": ["ナンパ", "街角ナンパ", "素人ナンパ"],
    "初撮り": ["初撮り", "初撮り素人"],
    "美少女": ["美少女"],
    "ギャル": ["ギャル", "黒ギャル"],
}

THEME_EXCLUDES = {
    "人妻・主婦": ["女子校生", "女子大生"],
    "女子大生": ["人妻・主婦", "人妻", "主婦", "熟女"],
    "女子校生": ["人妻・主婦", "人妻", "主婦", "熟女"],
    "熟女": ["女子校生", "女子大生"],
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


def get_maker(work: dict[str, Any]) -> str:
    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})
    maker_info = iteminfo.get("maker")

    if isinstance(maker_info, list) and maker_info:
        return maker_info[0].get("name", "")

    if isinstance(maker_info, dict):
        return maker_info.get("name", "")

    return ""


def normalize_text(text: Any) -> str:
    return str(text or "").strip()


def has_genre(required_genre: str | None, genres: list[str]) -> bool:
    if not required_genre:
        return True

    aliases = GENRE_ALIASES.get(required_genre, [required_genre])
    normalized_genres = [normalize_text(g) for g in genres]

    return any(alias in normalized_genres for alias in aliases)


def has_conflict_theme_genre(theme_genres: list[str], genres: list[str]) -> bool:
    for theme_genre in theme_genres:
        exclude_genres = THEME_EXCLUDES.get(theme_genre, [])

        for genre in genres:
            if genre in exclude_genres:
                return True

    return False


def detect_series(title: str) -> str:
    if not title:
        return "unknown"

    for pattern in SERIES_PATTERNS:
        if pattern in title:
            return pattern

    cleaned = re.sub(
        r"(No\.?\s*\d+|Vol\.?\s*\d+|File\s*\d+|第\d+弾).*",
        "",
        title,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r"[【\[].*$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return "unknown"

    # タイトル全文をログに出さないため、実体は内部制御用だけにする
    return f"title_prefix_{abs(hash(cleaned[:24]))}"


def get_recently_used_content_ids() -> set[str]:
    used_data = load_json("data/used_works.json", default={"works": []})
    used_works = used_data.get("works", [])
    today = datetime.now()

    recent_ids = set()

    for item in used_works:
        content_id = item.get("content_id")
        used_at = item.get("used_at")

        if not content_id or not used_at:
            continue

        try:
            used_date = datetime.strptime(used_at, "%Y-%m-%d")
        except Exception:
            continue

        if (today - used_date).days < DAYS_LIMIT:
            recent_ids.add(content_id)

    return recent_ids


def get_theme_genres(theme: dict[str, Any]) -> tuple[str, list[str]]:
    base_genre = theme.get("base_genre", "素人")

    if theme.get("theme_genres"):
        return base_genre, theme.get("theme_genres", [])

    if theme.get("theme_genre"):
        return base_genre, [theme.get("theme_genre")]

    required = theme.get("required", [])

    if required:
        theme_genres = [
            g for g in required
            if g != base_genre
        ]
        return base_genre, theme_genres

    return base_genre, []


def passes_theme_rules(
    scored: dict[str, Any],
    theme: dict[str, Any],
) -> bool:
    min_review_count = theme.get("min_review_count")

    if min_review_count is not None:
        if int(scored.get("review_count") or 0) < int(min_review_count):
            return False

    min_favorite_count = theme.get("min_favorite_count")

    if min_favorite_count is not None:
        if int(scored.get("favorite_count") or 0) < int(min_favorite_count):
            return False

    if theme.get("require_weekly_rank"):
        if not scored.get("weekly_rank"):
            return False

    if theme.get("require_monthly_rank"):
        if not scored.get("monthly_rank"):
            return False

    return True


def sort_scored_works(
    scored_works: list[dict[str, Any]],
    sort_key: str,
) -> list[dict[str, Any]]:
    if sort_key == "review_count":
        return sorted(
            scored_works,
            key=lambda x: (
                x.get("review_count") or 0,
                x.get("score") or 0,
            ),
            reverse=True,
        )

    if sort_key == "favorite_count":
        return sorted(
            scored_works,
            key=lambda x: (
                x.get("favorite_count") or 0,
                x.get("score") or 0,
            ),
            reverse=True,
        )

    if sort_key == "weekly_rank":
        return sorted(
            scored_works,
            key=lambda x: (
                x.get("weekly_rank") is not None,
                -(int(x.get("weekly_rank") or 999999)),
                x.get("score") or 0,
            ),
            reverse=True,
        )

    if sort_key == "monthly_rank":
        return sorted(
            scored_works,
            key=lambda x: (
                x.get("monthly_rank") is not None,
                -(int(x.get("monthly_rank") or 999999)),
                x.get("score") or 0,
            ),
            reverse=True,
        )

    return sorted(
        scored_works,
        key=lambda x: x.get("score") or 0,
        reverse=True,
    )


def main() -> None:
    theme = load_json("data/current_theme.json")
    scored_works = load_json("data/scored_works.json", default=[])
    candidate_works = load_json("data/selected_candidates.json", default=[])

    base_genre, theme_genres = get_theme_genres(theme)
    sort_key = theme.get("sort_key", "score")

    scored_works = sort_scored_works(scored_works, sort_key)

    candidate_map = {
        work.get("content_id"): work
        for work in candidate_works
        if work.get("content_id")
    }

    recently_used_ids = get_recently_used_content_ids()

    selected = []

    series_count = defaultdict(int)
    maker_count = defaultdict(int)

    skipped_used = 0
    skipped_no_candidate = 0
    skipped_no_base = 0
    skipped_no_theme = 0
    skipped_theme_rule = 0
    skipped_theme_conflict = 0
    skipped_series = 0
    skipped_maker = 0

    for scored in scored_works:
        content_id = scored.get("content_id")
        work = candidate_map.get(content_id)

        if not work:
            skipped_no_candidate += 1
            continue

        if content_id in recently_used_ids:
            skipped_used += 1
            continue

        if not passes_theme_rules(scored, theme):
            skipped_theme_rule += 1
            continue

        genres = get_genres(work)

        if not has_genre(base_genre, genres):
            skipped_no_base += 1
            continue

        if theme_genres:
            if not all(has_genre(g, genres) for g in theme_genres):
                skipped_no_theme += 1
                continue

        if has_conflict_theme_genre(theme_genres, genres):
            skipped_theme_conflict += 1
            continue

        title = scored.get("title") or work.get("title") or ""
        series = detect_series(title)
        maker = get_maker(work)

        if series_count[series] >= MAX_SERIES:
            skipped_series += 1
            continue

        if maker and maker_count[maker] >= MAX_MAKER:
            skipped_maker += 1
            continue

        selected.append({
            "content_id": content_id,
            "title": title,
            "score": scored.get("score"),
            "review_average": scored.get("review_average"),
            "review_count": scored.get("review_count"),
            "favorite_count": scored.get("favorite_count"),
            "weekly_rank": scored.get("weekly_rank"),
            "monthly_rank": scored.get("monthly_rank"),
            "base_genre": base_genre,
            "theme_genres": theme_genres,
            "theme_genre": theme_genres[0] if theme_genres else None,
            "theme_type": theme.get("type", "genre"),
            "sort_key": sort_key,
            "series": series,
            "maker": maker,
            "genres": genres,
            "url": scored.get("url") or work.get("url"),
            "image": scored.get("image") or work.get("image"),
        })

        series_count[series] += 1

        if maker:
            maker_count[maker] += 1

        if len(selected) >= TOP_N:
            break

    print(f"theme={theme.get('name')}")
    print(f"theme_type={theme.get('type', 'genre')}")
    print(f"sort_key={sort_key}")
    print(f"base_genre={base_genre}")
    print(f"theme_genres={theme_genres}")
    print(f"selected={len(selected)}")
    print(f"skipped_no_candidate={skipped_no_candidate}")
    print(f"skipped_used={skipped_used}")
    print(f"skipped_no_base={skipped_no_base}")
    print(f"skipped_no_theme={skipped_no_theme}")
    print(f"skipped_theme_rule={skipped_theme_rule}")
    print(f"skipped_theme_conflict={skipped_theme_conflict}")
    print(f"skipped_series={skipped_series}")
    print(f"skipped_maker={skipped_maker}")
    print(f"series_groups={len(series_count)}")
    print(f"maker_groups={len(maker_count)}")

    if len(selected) < MIN_SELECTED:
        raise Exception(f"Not enough selected works: {len(selected)}")

    save_json(WORKS_PATH, selected)


if __name__ == "__main__":
    main()
