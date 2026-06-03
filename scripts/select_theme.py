import json
import random
from collections import defaultdict
from datetime import datetime
from typing import Any

DAYS_LIMIT = 60

THEMES_PATH = "data/themes.json"
USED_THEMES_PATH = "data/used_themes.json"
CURRENT_THEME_PATH = "data/current_theme.json"

MIN_COUNT_HINT = 7

TYPE_WEIGHTS = {
    "genre": 40,
    "combo": 35,
    "review_count": 15,
    "favorite_count": 5,
    "ranking": 5,
}


def load_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_recently_used(theme_name: str, used_themes: list[dict[str, Any]]) -> bool:
    today = datetime.now()

    for used in used_themes:
        if used.get("name") != theme_name:
            continue

        used_at_raw = used.get("used_at")

        if not used_at_raw:
            continue

        try:
            used_at = datetime.strptime(used_at_raw, "%Y-%m-%d")
        except Exception:
            continue

        if (today - used_at).days < DAYS_LIMIT:
            return True

    return False


def weighted_choice_by_type(themes: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for theme in themes:
        theme_type = theme.get("type", "genre")
        grouped[theme_type].append(theme)

    available_types = list(grouped.keys())

    weights = [
        TYPE_WEIGHTS.get(theme_type, 10)
        for theme_type in available_types
    ]

    selected_type = random.choices(
        available_types,
        weights=weights,
        k=1,
    )[0]

    candidates = grouped[selected_type]

    candidates.sort(
        key=lambda x: x.get("count_hint", 0),
        reverse=True,
    )

    top_pool_size = min(20, len(candidates))
    top_pool = candidates[:top_pool_size]

    return random.choice(top_pool)


def main() -> None:
    themes = load_json(THEMES_PATH, default=[])
    used_data = load_json(USED_THEMES_PATH, default={"themes": []})
    used_themes = used_data.get("themes", [])

    available = []

    skipped_recent = 0
    skipped_low_count = 0

    for theme in themes:
        name = theme.get("name")

        if not name:
            continue

        count_hint = theme.get("count_hint", 0)

        if count_hint < MIN_COUNT_HINT:
            skipped_low_count += 1
            continue

        if is_recently_used(name, used_themes):
            skipped_recent += 1
            continue

        available.append(theme)

    if not available:
        raise Exception(
            "No available themes. Increase generated themes, lower MIN_COUNT_HINT, or shorten DAYS_LIMIT."
        )

    selected = weighted_choice_by_type(available)

    save_json(CURRENT_THEME_PATH, selected)

    type_counts = defaultdict(int)

    for theme in available:
        type_counts[theme.get("type", "genre")] += 1

    print(f"themes_total={len(themes)}")
    print(f"available={len(available)}")
    print(f"skipped_recent={skipped_recent}")
    print(f"skipped_low_count={skipped_low_count}")
    print("available_by_type:")
    print(json.dumps(dict(type_counts), ensure_ascii=False, indent=2))
    print(f"selected_type={selected.get('type', 'genre')}")
    print(f"selected_name={selected.get('name')}")
    print(f"count_hint={selected.get('count_hint')}")


if __name__ == "__main__":
    main()
