import json
import os
from google import genai

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

ARTICLE_PATH = "data/generated_article.md"

client = genai.Client(api_key=GEMINI_API_KEY)

with open("data/current_theme.json", "r", encoding="utf-8") as f:
    theme = json.load(f)

with open("data/selected_article_works.json", "r", encoding="utf-8") as f:
    works = json.load(f)

with open("data/reviews.json", "r", encoding="utf-8") as f:
    reviews = json.load(f)

prompt = f"""
あなたはSEO記事編集者です。
以下のテーマと作品データをもとに、WordPressに貼れる記事を作成してください。

条件:
- 露骨な描写は避ける
- 作品情報を整理する
- h2/h3を使う
- 冒頭に300〜600字の導入文
- 最後に総評
- 作品ごとに向いている人・注意点を簡潔に書く
- レビュー本文は引用しすぎず、傾向として要約する

テーマ:
{json.dumps(theme, ensure_ascii=False, indent=2)}

作品:
{json.dumps(works, ensure_ascii=False, indent=2)}

レビュー:
{json.dumps(reviews, ensure_ascii=False, indent=2)}
"""

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=prompt,
)

article = response.text.strip()

if not article:
    raise Exception("Gemini returned empty article")

with open(ARTICLE_PATH, "w", encoding="utf-8") as f:
    f.write(article)

print("article generated")
print(f"article_path={ARTICLE_PATH}")
