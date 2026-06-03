import json

EXCLUDE_KEYWORDS = [
    "BEST",
    "ベスト",
    "総集編",
    "総集",
    "VR",
    "4時間以上作品",
    "8時間以上作品",
    "16時間以上作品",
    "長尺",
    "福袋",
    "BOX",
    "DXBOX"
]

with open(
    "data/works.json",
    "r",
    encoding="utf-8"
) as f:
    works = json.load(f)

filtered = []

for work in works:

    title = work.get("title", "")

    genres = []

    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})

    for g in iteminfo.get("genre", []):
        genres.append(g.get("name", ""))

    text = title + " " + " ".join(genres)

    exclude = False

    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text.lower():
            exclude = True
            print(f"exclude: {title}")
            break

    if not exclude:
        filtered.append(work)

with open(
    "data/selected_candidates.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        filtered,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"works={len(works)}")
print(f"filtered={len(filtered)}")
