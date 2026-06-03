import json
import random

with open("data/themes.json", "r", encoding="utf-8") as f:
    themes = json.load(f)

with open("data/used_themes.json", "r", encoding="utf-8") as f:
    used = json.load(f)

available = []

for theme in themes:

    name = theme["name"]

    if name in used:
        continue

    available.append(theme)

if not available:
    print("no theme")
    exit()

selected = random.choice(available)

with open(
    "data/current_theme.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        selected,
        f,
        ensure_ascii=False,
        indent=2
    )

print(selected["name"])
