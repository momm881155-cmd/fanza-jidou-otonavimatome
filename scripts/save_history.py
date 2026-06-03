import json
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")

# ------------------
# theme
# ------------------

with open("data/current_theme.json", "r", encoding="utf-8") as f:
    current_theme = json.load(f)

with open("data/used_themes.json", "r", encoding="utf-8") as f:
    used_themes = json.load(f)

used_themes.setdefault("themes", [])

used_themes["themes"].append({
    "name": current_theme["name"],
    "used_at": today
})

with open("data/used_themes.json", "w", encoding="utf-8") as f:
    json.dump(
        used_themes,
        f,
        ensure_ascii=False,
        indent=2
    )

# ------------------
# works
# ------------------

with open(
    "data/selected_article_works.json",
    "r",
    encoding="utf-8"
) as f:
    selected_works = json.load(f)

with open(
    "data/used_works.json",
    "r",
    encoding="utf-8"
) as f:
    used_works = json.load(f)

used_works.setdefault("works", [])

for work in selected_works:

    used_works["works"].append({
        "content_id": work["content_id"],
        "title": work["title"],
        "used_at": today
    })

with open(
    "data/used_works.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        used_works,
        f,
        ensure_ascii=False,
        indent=2
    )

print("history saved")
