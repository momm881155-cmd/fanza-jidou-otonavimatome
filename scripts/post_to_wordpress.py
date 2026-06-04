import os
import re
import json
import base64
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

ARTICLE_PATH = DATA_DIR / "generated_article.md"
HISTORY_PATH = DATA_DIR / "article_history.json"

WP_SITE_URL = os.environ["WP_SITE_URL"].rstrip("/")
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

# 記事読み込み
with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# title抽出
title_match = re.search(
    r'<!--\s*title:\s*(.*?)\s*-->',
    content,
    flags=re.IGNORECASE
)

if not title_match:
    raise Exception("title not found")

title = title_match.group(1).strip()

# titleコメント除去
content = re.sub(
    r'<!--\s*title:\s*.*?\s*-->\s*',
    '',
    content,
    flags=re.IGNORECASE
)

# eye catch コメント除去
content = re.sub(
    r'<!--\s*eye_catch_image:.*?-->\s*',
    '',
    content,
    flags=re.IGNORECASE
)

content = re.sub(
    r'<!--\s*eye_catch_source:.*?-->\s*',
    '',
    content,
    flags=re.IGNORECASE
)

# WordPressへ下書き投稿
endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

payload = {
    "title": title,
    "content": content,
    "status": "draft"
}

token = base64.b64encode(
    f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode("utf-8")
).decode("utf-8")

headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "GitHubActions/1.0"
}

response = requests.post(
    endpoint,
    headers=headers,
    data=json.dumps(payload),
    timeout=60
)

if response.status_code not in [200, 201]:
    print(response.text)
    raise Exception(f"WordPress post failed: {response.status_code}")

post = response.json()

post_url = post.get("link")
post_id = post.get("id")

print("WordPress draft created")
print("post_id =", post_id)
print("post_url =", post_url)

# 履歴保存
try:
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)
except:
    history = []

history.append({
    "title": title,
    "url": post_url
})

with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print("history updated")
