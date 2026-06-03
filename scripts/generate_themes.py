import json

MIN_COUNT = 5

EXCLUDE_GENRES = {
    "ハイビジョン",
    "4K",
    "4時間以上作品",
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
    "単体作品"
}

with open("data/genre_counts.json", "r", encoding="utf-8") as f:
    genre_counts = json.load(f)

themes = []

for item in genre_counts:
    genre = item["genre"]
    count = item["count"]

    if count < MIN_COUNT:
        continue

    if genre in EXCLUDE_GENRES:
        continue

    if genre == "素人":
        continue

    themes.append({
        "name": f"素人×{genre}",
        "required": ["素人", genre],
        "count_hint": count
    })

with open("data/themes.json", "w", encoding="utf-8") as f:
    json.dump(themes, f, ensure_ascii=False, indent=2)

print(f"themes={len(themes)}")
