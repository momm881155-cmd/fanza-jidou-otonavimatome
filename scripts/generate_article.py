import os
import json
from pathlib import Path
from google import genai

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def load_json(name):
    path = DATA_DIR / name
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

current_theme = load_json("current_theme.json")
works = load_json("selected_article_works.json")
reviews = load_json("reviews.json")

prompt = f"""
あなたは成人向けアフィリエイトブログのSEO編集者です。

以下のテーマ・作品データ・レビュー傾向をもとに、
WordPressにそのまま貼れる記事本文をHTML形式で作成してください。

【記事方針】
・検索ユーザーが作品を比較しやすい記事にする
・作品情報の羅列ではなく比較と判断を重視する
・レビュー本文は引用せず評価傾向として要約する
・露骨な性的描写や行為の詳細は新規生成しない
・未成年を示唆する表現は禁止
・出力は記事本文のみ
・前置きや補足説明は禁止

【SEOタイトル形式】
素人×〇〇おすすめ10選｜サブタイトル

【記事構成】

<h1>SEO向けタイトル</h1>

導入文（400〜700文字）

<h2>今回のテーマと選定基準</h2>

テーマの特徴
選定基準
どんな人向けか

<h2>おすすめ作品一覧</h2>

各作品は以下の形式で出力する。

<h3>第1位：作品名</h3>

作品の特徴を2〜4段落で解説する。

<div class="information-box">
<strong>おすすめポイント</strong>
<ul>
<li>ポイント</li>
<li>ポイント</li>
<li>ポイント</li>
</ul>
</div>

<div class="alert-box">
<strong>気になるポイント</strong>
<ul>
<li>注意点</li>
<li>注意点</li>
</ul>
</div>

<div class="blank-box bb-key-color">
<strong>こんな人におすすめ</strong>
<ul>
<li>おすすめユーザー</li>
<li>おすすめユーザー</li>
<li>おすすめユーザー</li>
</ul>
</div>

<p class="btn-wrap btn-wrap-key-color">
<a href="作品URL" target="_blank" rel="nofollow sponsored noopener">FANZAで詳細を見る</a>
</p>

<hr>

<h2>【比較】今回紹介したおすすめ作品</h2>

以下の形式でHTMLテーブルを作成する。

<table>
<thead>
<tr>
<th>作品</th>
<th>特徴</th>
<th>おすすめ度</th>
</tr>
</thead>
<tbody>
...
</tbody>
</table>

<h2>【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>

比較しながら選び方を解説する。

<h2>関連記事</h2>

関連テーマ案を3件出力する。

【テーマ】
{json.dumps(current_theme, ensure_ascii=False, indent=2)}

【作品データ】
{json.dumps(works, ensure_ascii=False, indent=2)}

【レビュー情報】
{json.dumps(reviews, ensure_ascii=False, indent=2)}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

article = response.text

output_path = OUTPUT_DIR / "article.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(article)

print("記事生成完了:", output_path)
