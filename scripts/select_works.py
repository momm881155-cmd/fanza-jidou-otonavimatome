import json
import re
from collections import defaultdict
from datetime import datetime

TOP_N = 10
MIN_SELECTED = 7

MAX_SERIES = 2
MAX_MAKER = 3
DAYS_LIMIT = 60

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
        flags=re.IGNORECASE
    )

    cleaned = re.sub(r"[【\[].*$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned[:24] if cleaned else title[:24]


def get_recently_used_content_ids():
    try:
        with open("data/used_works.json", "r", encoding="utf-8") as f:
            used_data = json.load(f)
    except FileNotFoundError:
        return set()

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


with open("data/current_theme.json", "r", encoding="utf-8") as f:
    theme = json.load(f)

with open("data/scored_works.json", "r", encoding="utf-8") as f:
    scored_works = json.load(f)

with open("data/selected_candidates.json", "r", encoding="utf-8") as f:
    candidate_works = json.load(f)

required = theme.get("required", [])

candidate_map = {
    work.get("content_id"): work
    for work in candidate_works
}

recently_used_ids = get_recently_used_content_ids()

selected = []

series_count = defaultdict(int)
maker_count = defaultdict(int)

skipped_used = 0
skipped_series = 0
skipped_maker = 0

for scored in scored_works:
    content_id = scored.get("content_id")
    work = candidate_map.get(content_id)

    if not work:
        continue

    if content_id in recently_used_ids:
        skipped_used += 1
        continue

    genres = get_genres(work)

    if not all(req in genres for req in required):
        continue

    title = scored.get("title") or ""
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
        "series": series,
        "maker": maker,
        "genres": genres,
        "url": scored.get("url"),
        "image": scored.get("image")
    })

    series_count[series] += 1

    if maker:
        maker_count[maker] += 1

    if len(selected) >= TOP_N:
        break


print(f"theme: {theme.get('name')}")
print(f"selected: {len(selected)}")
print(f"skipped_used: {skipped_used}")
print(f"skipped_series: {skipped_series}")
print(f"skipped_maker: {skipped_maker}")
print("series_count:")
print(json.dumps(dict(series_count), ensure_ascii=False, indent=2))
print("maker_count:")
print(json.dumps(dict(maker_count), ensure_ascii=False, indent=2))

if len(selected) < MIN_SELECTED:
    raise Exception(f"Not enough selected works: {len(selected)}")

with open("data/selected_article_works.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)
