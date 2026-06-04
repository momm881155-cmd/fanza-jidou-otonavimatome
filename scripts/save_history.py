import json
from datetime import datetime
from typing import Any

CURRENT_THEME_PATH = "data/current_theme.json"
SELECTED_WORKS_PATH = "data/selected_article_works.json"
USED_THEMES_PATH = "data/used_themes.json"
USED_WORKS_PATH = "data/used_works.json"
ARTICLE_PATH = "data/generated_article.md"

today = datetime.now().strftime("%Y-%m-%d")


def load_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_article_exists() -> None:
    try:
        with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
            article = f.read().strip()
    except FileNotFoundError:
        raise Exception("generated_article.md not found. History will not be saved.")

    if not article:
        raise Exception("generated_article.md is empty. History will not be saved.")


def save_theme_history() -> int:
    current_theme = load_json(CURRENT_THEME_PATH, default={})
    used_themes = load_json(USED_THEMES_PATH, default={"themes": []})

    used_themes.setdefault("themes", [])

    theme_name = current_theme.get("name")

    if not theme_name:
        print("theme_skipped=1")
        return 0

    existing_keys = {
        (
            item.get("name"),
            item.get("used_at"),
        )
        for item in used_themes["themes"]
    }

    key = (theme_name, today)

    if key in existing_keys:
        print("theme_already_saved=1")
        save_json(USED_THEMES_PATH, used_themes)
        return 0

    used_themes["themes"].append({
        "name": theme_name,
        "type": current_theme.get("type"),
        "base_genre": current_theme.get("base_genre"),
        "theme_genre": current_theme.get("theme_genre"),
        "theme_genres": current_theme.get("theme_genres"),
        "count_hint": current_theme.get("count_hint"),
        "used_at": today,
    })

    save_json(USED_THEMES_PATH, used_themes)

    return 1


def save_work_history() -> int:
    selected_works = load_json(SELECTED_WORKS_PATH, default=[])
    used_works = load_json(USED_WORKS_PATH, default={"works": []})

    used_works.setdefault("works", [])

    existing_ids = {
        item.get("content_id")
        for item in used_works["works"]
        if item.get("content_id")
    }

    added = 0

    for work in selected_works:
        content_id = work.get("content_id")

        if not content_id:
            continue

        if content_id in existing_ids:
            continue

        used_works["works"].append({
            "content_id": content_id,
            "theme_name": work.get("theme_name"),
            "theme_type": work.get("theme_type"),
            "base_genre": work.get("base_genre"),
            "theme_genre": work.get("theme_genre"),
            "theme_genres": work.get("theme_genres"),
            "used_at": today,
        })

        existing_ids.add(content_id)
        added += 1

    save_json(USED_WORKS_PATH, used_works)

    return added


def main() -> None:
    validate_article_exists()

    theme_added = save_theme_history()
    works_added = save_work_history()

    print("history saved")
    print(f"theme_added={theme_added}")
    print(f"works_added={works_added}")


if __name__ == "__main__":
    main()
