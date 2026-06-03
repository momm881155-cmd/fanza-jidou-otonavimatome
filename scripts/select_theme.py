import json
import random
from datetime import datetime

DAYS_LIMIT = 60

with open("data/themes.json", "r", encoding="utf-8") as f:
    themes = json.load(f)

with open("data/used_themes.json", "r", encoding="utf-8") as f:
    used_data = json.load(f)

used_themes = used_data.get("themes", [])

available = []

today = datetime.now()

for theme in themes:
    name = theme["name"]

    recently_used = False

    for used in used_themes:
        if used.get("name") != name:
            continue

        try:
            used_at = datetime.strptime(
                used["used_at"],
                "%Y-%m-%d"
            )

            if (today - used_at).days < DAYS_LIMIT:
                recently_used = True
                break

        except Exception:
            pass

    if recently_used:
        continue

    available.append(theme)

if not available:
    print("all themes used")
    available = themes

selected = random.choice(available)

with open("data/current_theme.json", "w", encoding="utf-8") as f:
    json.dump(
        selected,
        f,
        ensure_ascii=False,
        indent=2
    )

print(selected["name"])
