import json
from itertools import combinations

MIN_GENRE_COUNT = 10
MIN_THEME_WORKS = 7

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
    "デジモ"
}

def get_genres(work):
    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})
    return [
        g.get("name")
        for g in iteminfo.get("genre", [])
        if g.get("name")
    ]

with open("data/genre_counts.json", "r", encoding="utf-8") as f:
    genre_counts = json.load(f)

with open("data/selected_candidates.json", "r", encoding="utf-8") as f:
    works = json.load(f)

genre_pool = []

for item in genre_counts:
    genre = item["genre"]
    count = item["count"]

    if count < MIN_GENRE_COUNT:
        continue

    if genre in EXCLUDE_GENRES:
        continue

    if genre == "素人":
        continue

    genre_pool.append({
        "name": genre,
        "count": count
    })

raw_themes = []

for g in genre_pool:
    raw_themes.append({
        "name": f"素人×{g['name']}",
        "required": ["素人", g["name"]]
    })

for g1, g2 in combinations(genre_pool, 2):
    raw_themes.append({
        "name": f"素人×{g1['name']}×{g2['name']}",
        "required": ["素人", g1["name"], g2["name"]]
    })

themes = []

for theme in raw_themes:
    required = theme["required"]
    match_count = 0

    for work in works:
        genres = get_genres(work)

        if all(req in genres for req in required):
            match_count += 1

    if match_count < MIN_THEME_WORKS:
        continue

    theme["count_hint"] = match_count
    themes.append(theme)

themes.sort(key=lambda x: x["count_hint"], reverse=True)

with open("data/themes.json", "w", encoding="utf-8") as f:
    json.dump(themes, f, ensure_ascii=False, indent=2)

print(f"themes={len(themes)}")
