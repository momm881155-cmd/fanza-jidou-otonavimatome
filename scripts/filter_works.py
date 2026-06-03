import json

EXCLUDE_KEYWORDS = [
    "BEST",
    "ベスト",
    "総集編",
    "総集",
    "VR",
    "4時間以上",
    "8時間以上",
    "16時間以上",
    "長尺",
    "複数話",
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
    genres = work.get("genres", [])

    text = title + " " + " ".join(genres)

    exclude = False

    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text.lower():
            exclude = True
            break

    if exclude:
        continue

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
