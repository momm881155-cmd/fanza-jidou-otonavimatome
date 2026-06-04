import os
import re
import json
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

ARTICLE_PATH = DATA_DIR / "generated_article.md"
HISTORY_PATH = DATA_DIR / "article_history.json"

WP_SITE_URL = os.environ["WP_SITE_URL"].rstrip("/")
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

token = base64.b64encode(
    f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode("utf-8")
).decode("utf-8")

headers_json = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "GitHubActions/1.0"
}

headers_auth = {
    "Authorization": f"Basic {token}",
    "Accept": "application/json",
    "User-Agent": "GitHubActions/1.0"
}


def extract_comment(name, text):
    m = re.search(
        rf'<!--\s*{re.escape(name)}:\s*(.*?)\s*-->',
        text,
        flags=re.IGNORECASE | re.DOTALL
    )
    return m.group(1).strip() if m else ""


def remove_comment(name, text):
    return re.sub(
        rf'<!--\s*{re.escape(name)}:\s*.*?\s*-->\s*',
        '',
        text,
        flags=re.IGNORECASE | re.DOTALL
    )


def upload_featured_image(image_url, title="featured-image"):
    if not image_url:
        return None

    img_res = requests.get(
        image_url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=60
    )

    if img_res.status_code != 200:
        print("Image download failed:", img_res.status_code, image_url)
        return None

    parsed = urlparse(image_url)
    filename = os.path.basename(parsed.path) or "featured-image.jpg"

    content_type = img_res.headers.get("Content-Type")
    if not content_type or "image" not in content_type:
        guessed, _ = mimetypes.guess_type(filename)
        content_type = guessed or "image/jpeg"

    media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"

    media_headers = {
        "Authorization": f"Basic {token}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": content_type,
        "Accept": "application/json",
        "User-Agent": "GitHubActions/1.0"
    }

    media_res = requests.post(
        media_endpoint,
        headers=media_headers,
        data=img_res.content,
        timeout=120
    )

    if media_res.status_code not in [200, 201]:
        print("Media upload failed:", media_res.status_code)
        print(media_res.text)
        return None

    media = media_res.json()
    media_id = media.get("id")

    if media_id:
        alt_payload = {
            "alt_text": title,
            "caption": title,
            "description": title
        }
        requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/media/{media_id}",
            headers=headers_json,
            data=json.dumps(alt_payload),
            timeout=60
        )

    return media_id


# 記事読み込み
with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# コメント抽出
title = extract_comment("title", content)
eye_catch_image = extract_comment("eye_catch_image", content)
eye_catch_source = extract_comment("eye_catch_source", content)

if not title:
    raise Exception("title not found")

# コメント除去
content = remove_comment("title", content)
content = remove_comment("eye_catch_image", content)
content = remove_comment("eye_catch_source", content)

# アイキャッチ画像アップロード
featured_media_id = upload_featured_image(
    eye_catch_image,
    eye_catch_source or title
)

# WordPressへ投稿
endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

payload = {
    "title": title,
    "content": content,
    "status": "publish"
}

if featured_media_id:
    payload["featured_media"] = featured_media_id

response = requests.post(
    endpoint,
    headers=headers_json,
    data=json.dumps(payload),
    timeout=60
)

if response.status_code not in [200, 201]:
    print(response.text)
    raise Exception(f"WordPress post failed: {response.status_code}")

post = response.json()

post_url = post.get("link")
post_id = post.get("id")

print("WordPress post created")
print("post_id =", post_id)
print("post_url =", post_url)
print("featured_media_id =", featured_media_id)

# 履歴保存
try:
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)
except Exception:
    history = []

history.append({
    "title": title,
    "url": post_url
})

with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print("history updated")
