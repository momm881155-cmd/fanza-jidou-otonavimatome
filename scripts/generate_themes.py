import json
from itertools import combinations

MIN_COUNT = 10

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

with open("data/genre_counts.json", "r", encoding="utf-8") as f:
    genre_counts = json.load(f)

genres = []

for item in genre_counts:

    genre = item["genre"]
    count = item["count"]

    if count < MIN_COUNT:
        continue

    if genre in EXCLUDE_GENRES:
        continue

    if genre == "素人":
        continue

    genres.append({
        "name": genre,
        "count": count
    })

themes = []

# 単独テーマ

for g in genres:

    themes.append({
        "name": f"素人×{g['name']}",
        "required": ["素人", g["name"]],
        "count_hint": g["count"]
    })

# 複合テーマ

for g1, g2 in combinations(genres, 2):

    themes.append({
        "name": f"素人×{g1['name']}×{g2['name']}",
        "required": [
            "素人",
            g1["name"],
            g2["name"]
        ],
        "count_hint": min(
            g1["count"],
            g2["count"]
        )
    })

with open(
    "data/themes.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        themes,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"themes={len(themes)}")
