import json
import re
from collections import defaultdict

TOP_N = 10

MAX_SERIES = 2
MAX_MAKER = 3

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

    # No.246 / Vol.9 / File25 以降を削って、同系統タイトルをまとめる
    cleaned = re.sub(r"(No\.?\s*\d+|Vol\.?\s*\d+|File\s*\d+|第\d+弾).*", "", title, flags=re.IGNORECASE)

    # 記号以降が長い場合も、先頭だけでシリーズ判定
    cleaned = re.sub(r"[【\[].*$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned[:24] if cleaned else title[:24]


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

selected = []

series_count = defaultdict(int)
maker_count = defaultdict(int)

skipped_series = 0
skipped_maker = 0

for scored in scored_works:
    content_id = scored.get("content_id")
    work = candidate_map.get(content_id)

    if not work:
        continue

    genres = get_genres(work)

    # テーマ必須ジャンルを全部持っている作品だけ通す
    if not all(req in genres for req in required):
        continue

    title = scored.get("title") or ""
    series = detect_series(title)
    maker = get_maker(work)

    # 同一シリーズ・企画の偏り防止
    if series_count[series] >= MAX_SERIES:
        skipped_series += 1
        continue

    # 同一メーカーの偏り防止
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


with open("data/selected_article_works.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)


print(f"theme: {theme.get('name')}")
print(f"selected: {len(selected)}")
print(f"skipped_series: {skipped_series}")
print(f"skipped_maker: {skipped_maker}")
print("series_count:")
print(json.dumps(dict(series_count), ensure_ascii=False, indent=2))
print("maker_count:")
print(json.dumps(dict(maker_count), ensure_ascii=False, indent=2))
