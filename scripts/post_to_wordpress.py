import os
import re
import json
import base64
import mimetypes
import time
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

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137 Safari/537.36"

headers_json = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": UA,
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


def parse_json_response(res, label):
    print(f"{label} STATUS =", res.status_code)
    print(f"{label} RESPONSE =", res.text[:3000])

    try:
        return res.json()
    except Exception:
        raise Exception(f"{label} returned non-JSON response")


def is_imunify_block(data):
    if not isinstance(data, dict):
        return False

    msg = str(data.get("message", ""))
    return (
        "Imunify360" in msg
        or "bot-protection" in msg
        or "Access denied" in msg
    )


def post_json_with_retry(url, payload, label, retries=5):
    last_data = None
    last_status = None

    for attempt in range(retries):
        print(f"{label} TRY {attempt + 1}/{retries}")

        res = requests.post(
            url,
            headers=headers_json,
            data=json.dumps(payload),
            timeout=120
        )

        data = parse_json_response(res, label)
        last_data = data
        last_status = res.status_code

        if res.status_code in [200, 201] and isinstance(data, dict) and data.get("id"):
            print(f"{label} SUCCESS")
            return data

        if is_imunify_block(data):
            wait = (attempt + 1) * 30
            print(f"Imunify360 detected on {label}. Retry after {wait} seconds...")
            time.sleep(wait)
            continue

        raise Exception(f"{label} failed: {res.status_code}\n{data}")

    raise Exception(f"{label} failed after retries. status={last_status}, data={last_data}")


def upload_media_binary_with_retry(endpoint, media_headers, image_bytes, retries=5):
    last_data = None
    last_status = None

    for attempt in range(retries):
        print(f"MEDIA UPLOAD TRY {attempt + 1}/{retries}")

        res = requests.post(
            endpoint,
            headers=media_headers,
            data=image_bytes,
            timeout=120
        )

        data = parse_json_response(res, "MEDIA UPLOAD")
        last_data = data
        last_status = res.status_code

        if res.status_code in [200, 201] and isinstance(data, dict) and data.get("id"):
            print("MEDIA UPLOAD SUCCESS")
            return data

        if is_imunify_block(data):
            wait = (attempt + 1) * 30
            print(f"Imunify360 detected on MEDIA UPLOAD. Retry after {wait} seconds...")
            time.sleep(wait)
            continue

        raise Exception(f"Media upload failed: {res.status_code}\n{data}")

    raise Exception(f"Media upload failed after retries. status={last_status}, data={last_data}")


def upload_featured_image(image_url, title="featured-image"):
    if not image_url:
        print("No eye_catch_image found")
        return None

    print("eye_catch_image =", image_url)

    img_res = requests.get(
        image_url,
        headers={"User-Agent": UA},
        timeout=60
    )

    print("IMAGE DOWNLOAD STATUS =", img_res.status_code)

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
        "User-Agent": UA,
    }

    media = upload_media_binary_with_retry(
        media_endpoint,
        media_headers,
        img_res.content,
        retries=5
    )

    media_id = media.get("id")

    if not media_id:
        print("Media uploaded but id not found")
        return None

    alt_payload = {
        "alt_text": title,
        "caption": title,
        "description": title
    }

    try:
        alt_res = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/media/{media_id}",
            headers=headers_json,
            data=json.dumps(alt_payload),
            timeout=60
        )
        print("MEDIA ALT STATUS =", alt_res.status_code)
        print("MEDIA ALT RESPONSE =", alt_res.text[:1000])
    except Exception as e:
        print("MEDIA ALT update failed but ignored:", e)

    return media_id


# 記事読み込み
with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# コメント抽出
title = extract_comment("title", content)
eye_catch_image = extract_comment("eye_catch_image", content)
eye_catch_source = extract_comment("eye_catch_source", content)

print("TITLE =", title)
print("EYE_CATCH_IMAGE =", eye_catch_image)

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
    "content": {
        "raw": content
    },
    "status": "publish"
}

if featured_media_id:
    payload["featured_media"] = featured_media_id

post = post_json_with_retry(
    endpoint,
    payload,
    "POST CREATE",
    retries=5
)

post_url = post.get("link")
post_id = post.get("id")

if not post_id:
    raise Exception("WordPress post created response has no id. Check POST CREATE RESPONSE above.")

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