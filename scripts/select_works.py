import json
import re
from collections import defaultdict
from datetime import datetime

TOP_N = 10
MIN_SELECTED = 7

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
    "素人": [
        "素人",
        "しろうと",
        "シロウト",
        "応募素人",
        "初撮り",
        "素人娘",
    ],
    "人妻・主婦": [
        "人妻・主婦",
        "人妻",
        "主婦",
        "奥様",
        "既婚者",
    ],
    "女子大生": [
        "女子大生",
        "大学生",
    ],
    "熟女": [
        "熟女",
    ],
    "ナンパ": [
        "ナンパ",
        "街角ナンパ",
        "素人ナンパ",
    ],
    "初撮り": [
        "初撮り",
        "初撮り素人",
    ],
    "美少女": [
        "美少女",
    ],
    "ギャル": [
        "ギャル",
        "黒ギャル",
    ],
}

THEME_EXCLUDES = {
    "人妻・主婦": [
        "女子校生",
        "女子大生",
    ],
    "女子大生": [
        "人妻・主婦",
        "人妻",
        "主婦",
        "熟女",
    ],
    "女子校生": [
        "人妻・主婦",
        "人妻",
        "主婦",
        "熟女",
    ],
    "熟女": [
        "女子校生",
        "女子大生",
    ],
}


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_genres(work):
    genres = []
    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})

    for genre in iteminfo.get("genre", []):
        name = genre.get("name")
        if name:
            genres.append(name)

    return genres


def get_maker(work):
    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})
    maker_info = iteminfo.get("maker")

    if isinstance(maker_info, list) and maker_info:
        return maker_info[0].get("name", "")

    if isinstance(maker_info, dict):
        return maker_info.get("name", "")

    return ""


def normalize_text(text):
    if not text:
        return ""

    return str(text).strip()


def has_genre(required_genre, genres):
    if not required_genre:
        return True

    aliases = GENRE_ALIASES.get(required_genre, [required_genre])
    normalized_genres = [normalize_text(g) for g in genres]

    for alias in aliases:
        if alias in normalized_genres:
            return True

    return False


def has_conflict_theme_genre(theme_genre, genres):
    exclude_genres = THEME_EXCLUDES.get(theme_genre, [])

    for genre in genres:
        if genre in exclude_genres:
            return True

    return False


def detect_series(title):
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

    return cleaned[:24] if cleaned else title[:24]


def get_recently_used_content_ids():
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


def get_theme_info(theme):
    """
    新形式:
    {
      "name": "素人×人妻・主婦おすすめ10選",
      "base_genre": "素人",
      "theme_genre": "人妻・主婦"
    }

    旧形式:
    {
      "name": "...",
      "required": ["素人", "人妻・主婦"]
    }
    """

    base_genre = theme.get("base_genre")
    theme_genre = theme.get("theme_genre")

    if base_genre or theme_genre:
        return base_genre or "素人", theme_genre

    required = theme.get("required", [])

    if "素人" in required:
        others = [g for g in required if g != "素人"]
        return "素人", others[0] if others else None

    if required:
        return "素人", required[0]

    return "素人", None


def main():
    theme = load_json("data/current_theme.json")
    scored_works = load_json("data/scored_works.json")
    candidate_works = load_json("data/selected_candidates.json")

    base_genre, theme_genre = get_theme_info(theme)

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

        genres = get_genres(work)

        if not has_genre(base_genre, genres):
            skipped_no_base += 1
            continue

        if theme_genre and not has_genre(theme_genre, genres):
            skipped_no_theme += 1
            continue

        if theme_genre and has_conflict_theme_genre(theme_genre, genres):
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
            "base_genre": base_genre,
            "theme_genre": theme_genre,
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

    print(f"theme: {theme.get('name')}")
    print(f"base_genre: {base_genre}")
    print(f"theme_genre: {theme_genre}")
    print(f"selected: {len(selected)}")
    print(f"skipped_no_candidate: {skipped_no_candidate}")
    print(f"skipped_used: {skipped_used}")
    print(f"skipped_no_base: {skipped_no_base}")
    print(f"skipped_no_theme: {skipped_no_theme}")
    print(f"skipped_theme_conflict: {skipped_theme_conflict}")
    print(f"skipped_series: {skipped_series}")
    print(f"skipped_maker: {skipped_maker}")
    print("series_count:")
    print(json.dumps(dict(series_count), ensure_ascii=False, indent=2))
    print("maker_count:")
    print(json.dumps(dict(maker_count), ensure_ascii=False, indent=2))

    if len(selected) < MIN_SELECTED:
        raise Exception(f"Not enough selected works: {len(selected)}")

    save_json(WORKS_PATH, selected)


if __name__ == "__main__":
    main()
