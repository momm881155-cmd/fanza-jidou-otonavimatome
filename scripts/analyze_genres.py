import json
from collections import Counter

with open("data/works.json", "r", encoding="utf-8") as f:
    works = json.load(f)

counter = Counter()

for work in works:
    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})

    for genre in iteminfo.get("genre", []):
        name = genre.get("name")
        if name:
            counter[name] += 1

genres = []

for name, count in counter.most_common():
    genres.append({
        "genre": name,
        "count": count
    })

with open(
    "data/genre_counts.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        genres,
        f,
        ensure_ascii=False,
        indent=2
    )

print("saved genre_counts.json")
