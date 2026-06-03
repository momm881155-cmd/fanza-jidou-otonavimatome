import json

TOP_N = 10

def get_genres(work):
    genres = []

    raw = work.get("raw", {})
    iteminfo = raw.get("iteminfo", {})

    for genre in iteminfo.get("genre", []):
        name = genre.get("name")
        if name:
            genres.append(name)

    return genres

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

for scored in scored_works:
    content_id = scored.get("content_id")
    work = candidate_map.get(content_id)

    if not work:
        continue

    genres = get_genres(work)

    ok = True
    for req in required:
        if req not in genres:
            ok = False
            break

    if not ok:
        continue

    selected.append({
        "content_id": content_id,
        "title": scored.get("title"),
        "score": scored.get("score"),
        "review_average": scored.get("review_average"),
        "review_count": scored.get("review_count"),
        "favorite_count": scored.get("favorite_count"),
        "weekly_rank": scored.get("weekly_rank"),
        "genres": genres,
        "url": scored.get("url"),
        "image": scored.get("image")
    })

    if len(selected) >= TOP_N:
        break

with open("data/selected_article_works.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

print(f"theme: {theme.get('name')}")
print(f"selected: {len(selected)}")
