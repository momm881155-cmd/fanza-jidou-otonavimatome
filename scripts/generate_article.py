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
WordPressにそのまま貼れる記事本文を作成してください。

【最重要ルール】
・出力は記事本文のみ
・前置きや説明は不要
・h2タグを使う
・作品見出しは必ず shortコード [fanza_heading] を使う
・作品情報表示は必ず shortコード [fanza_item] を使う
・作品ボタンは必ず shortコード [fanza_button] を使う
・レビュー本文の直接引用は禁止
・レビューは評価傾向として要約する
・露骨な性的描写や行為の詳細は新規生成しない
・未成年を示唆する表現は禁止
・作品情報の羅列ではなく、比較・判断・向き不向きを重視する

【ショートコードルール】

各作品の冒頭は必ず以下の形式にする。

[fanza_heading number="01" title="作品名"]
[fanza_item cid="content_id"]

numberは順位に合わせて01、02、03のように2桁にする。
titleには作品データのtitleをそのまま入れる。
cidには作品データのcontent_idを入れる。

作品紹介の最後には必ず以下を入れる。

[fanza_button url="作品URL" text="動画を見る"]

urlには作品データのurlを入れる。

【記事構成】

<h1>SEO向けタイトル</h1>

導入文 400〜700字

<h2>今回のテーマと選定基準</h2>

<p>今回のテーマの特徴、選定基準、どんな人向けかを説明する。</p>

<h2>おすすめ作品一覧</h2>

各作品は以下の形式で出力する。

[fanza_heading number="01" title="作品名"]
[fanza_item cid="content_id"]

<p>作品の特徴を2〜4段落で解説する。</p>

<h3>おすすめポイント</h3>
<ul>
<li>ポイント</li>
<li>ポイント</li>
<li>ポイント</li>
</ul>

<h3>気になるポイント</h3>
<ul>
<li>注意点</li>
<li>注意点</li>
</ul>

<h3>こんな人におすすめ</h3>
<ul>
<li>おすすめユーザー</li>
<li>おすすめユーザー</li>
<li>おすすめユーザー</li>
</ul>

[fanza_button url="作品URL" text="動画を見る"]

<h2>【比較】今回紹介したおすすめ作品</h2>

<table>
<thead>
<tr>
<th>作品</th>
<th>特徴</th>
<th>おすすめ度</th>
</tr>
</thead>
<tbody>
<tr>
<td>作品名</td>
<td>特徴を簡潔に記載</td>
<td>★★★★★</td>
</tr>
</tbody>
</table>

<h2>【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>

<p>今回の作品の選び方をまとめる。</p>

<h2>関連記事</h2>
<ul>
<li>関連テーマ案1</li>
<li>関連テーマ案2</li>
<li>関連テーマ案3</li>
</ul>

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
