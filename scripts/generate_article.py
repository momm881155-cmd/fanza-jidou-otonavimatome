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

style_sample_path = DATA_DIR / "style_sample.txt"

if style_sample_path.exists():
    with open(style_sample_path, "r", encoding="utf-8") as f:
        style_sample = f.read()
else:
    style_sample = ""

prompt = f"""
あなたは成人向けアフィリエイトブログのSEO編集者です。

以下のテーマ・作品データ・レビュー傾向・参考記事をもとに、
WordPressにそのまま貼れる記事本文を作成してください。

【最重要ルール】
・出力は記事本文のみ
・前置きや説明は不要
・WordPressのコードエディターに貼れる形式で出力する
・h2/h3/h4タグを使う
・作品見出しは必ずショートコード [fanza_heading] を使う
・作品情報表示は必ずショートコード [fanza_item] を使う
・作品ボタンは必ずショートコード [fanza_button] を使う
・レビュー本文の直接引用は禁止
・レビューは評価傾向として要約する
・露骨な性的描写や行為の詳細は新規生成しない
・未成年を示唆する表現は禁止
・作品情報の羅列ではなく、比較・判断・向き不向きを重視する
・参考記事の文章をコピーしない
・参考記事の作品名、URL、品番、固有名詞を流用しない
・参考記事は文体、構成、装飾、比較表、総評の作り方だけ参考にする

【参考記事から学習すること】
以下を優先して再現する。

・導入文で読者の悩みを代弁する
・仕事終わり、疲れた夜、迷っている読者に向けた導入にする
・作品ごとの違いを比較して選びやすくする
・おすすめポイント、気になるポイント、こんな人におすすめを必ず分ける
・比較表で最後に判断しやすくする
・総評で「迷ったらどれを選ぶべきか」を示す
・関連記事導線を自然に置く
・[fanza_heading]、[fanza_item]、[fanza_button] の配置を参考記事と同じ流れにする

【ショートコードルール】

各作品の冒頭は必ず以下の形式にする。

<!-- wp:shortcode -->
[fanza_heading number="01" title="作品名"]
<!-- /wp:shortcode -->

<!-- wp:shortcode -->
[fanza_item cid="content_id"]
<!-- /wp:shortcode -->

作品紹介の最後には必ず以下を入れる。

<!-- wp:shortcode -->
[fanza_button url="作品URL" text="動画を見る"]
<!-- /wp:shortcode -->

titleには作品データのtitleをそのまま入れる。
cidには作品データのcontent_idを入れる。
urlには作品データのurlを入れる。

【順位ルール】

作品データの並び順をランキング順位とする。

1件目 → number="01"
2件目 → number="02"
3件目 → number="03"
4件目 → number="04"
5件目 → number="05"
6件目 → number="06"
7件目 → number="07"
8件目 → number="08"
9件目 → number="09"
10件目 → number="10"

作品数が5件なら01〜05。
作品数が7件なら01〜07。
作品数が10件なら01〜10。

numberは固定値を使わず、必ず順位に応じて自動採番すること。

【装飾ルール】

おすすめポイントは以下の形式。

<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">おすすめポイント</h4>
<!-- /wp:heading -->

<!-- wp:list {{"extraBorder":"blank-box-blue","extraStyle":"icon-list-circle"}} -->
<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-circle has-list-style">
<li>...</li>
<li>...</li>
<li>...</li>
</ul>
<!-- /wp:list -->

気になるポイントは以下の形式。

<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">気になるポイント</h4>
<!-- /wp:heading -->

<!-- wp:list {{"extraBorder":"blank-box-blue","extraStyle":"icon-list-cross"}} -->
<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-cross has-list-style">
<li>...</li>
<li>...</li>
</ul>
<!-- /wp:list -->

こんな人におすすめは以下の形式。

<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">こんな人におすすめ</h4>
<!-- /wp:heading -->

<!-- wp:list {{"extraBorder":"blank-box-blue","extraStyle":"icon-list-thumb-up"}} -->
<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-thumb-up has-list-style">
<li>...</li>
<li>...</li>
<li>...</li>
</ul>
<!-- /wp:list -->

作品ごとの区切りには以下を入れる。

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

【記事構成】

導入文 400〜700字。
読者の悩みを代弁し、今回のテーマで何を比較する記事なのかを説明する。

<!-- wp:heading {{"textAlign":"center"}} -->
<h2 class="wp-block-heading has-text-align-center">テーマに合うおすすめ作品一覧</h2>
<!-- /wp:heading -->

各作品をランキング順に紹介する。

作品ごとに以下を必ず入れる。

1. [fanza_heading]
2. [fanza_item]
3. 作品紹介本文 2〜4段落
4. おすすめポイント
5. 気になるポイント
6. こんな人におすすめ
7. [fanza_button]
8. 区切り線

<!-- wp:heading -->
<h2 class="wp-block-heading">【比較】今回紹介したおすすめ作品</h2>
<!-- /wp:heading -->

比較表の前に、比較基準を1段落で説明する。

比較表は以下のWordPressブロック形式で出力する。

<!-- wp:table {{"className":"review-table"}} -->
<figure class="wp-block-table review-table"><table class="has-fixed-layout"><thead><tr><th>作品</th><th>特徴</th><th>おすすめ度</th></tr></thead><tbody>
<tr><td>作品名</td><td>特徴</td><td>★★★★★<br>おすすめ理由</td></tr>
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading -->
<h2 class="wp-block-heading">【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>
<!-- /wp:heading -->

総評では、今回のテーマでどんな人がどの作品を選ぶべきかを整理する。
特におすすめの作品を2〜3本挙げて、選ぶ理由を説明する。

<!-- wp:heading -->
<h2 class="wp-block-heading">関連記事</h2>
<!-- /wp:heading -->

関連記事は、現時点ではURLを作らず、関連テーマ案を3件だけ出力する。
存在しないURLは絶対に作らない。

【参考記事本文】
{style_sample[:8000]}

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

print("===== GEMINI RESPONSE =====")
print(response)

if response is None:
    raise Exception("Gemini returned None")

if not getattr(response, "text", None):
    raise Exception(f"Gemini returned no text: {response}")

article = response.text.strip()

if not article:
    raise Exception("Gemini returned empty article")

output_path = OUTPUT_DIR / "article.html"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(article)

print("記事生成完了")
print(f"article_path={output_path}")
