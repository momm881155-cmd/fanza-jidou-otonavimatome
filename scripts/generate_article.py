import os
import json
import re
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

def sanitize_text(text):
    if text is None:
        return text
    text = str(text)

    replacements = {
        "中出し": "フィニッシュ",
        "生中出し": "フィニッシュ",
        "生ハメ": "密着シーン",
        "SEX": "親密シーン",
        "セックス": "親密シーン",
        "フェラ": "奉仕シーン",
        "チンポ": "男性向け要素",
        "チ●ポ": "男性向け要素",
        "オマ○コ": "女性向け要素",
        "マ〇コ": "女性向け要素",
        "潮吹き": "リアクション",
        "顔射": "フィニッシュ演出",
        "ごっくん": "奉仕描写",
        "精子": "フィニッシュ描写",
        "射精": "フィニッシュ",
        "巨根": "男性向け要素",
        "乳首": "身体表現",
        "爆乳": "グラマラス",
        "巨乳": "グラマラス",
        "ハメ撮り": "主観系",
        "オナニー": "ソロシーン",
        "3P": "複数人シーン",
        "4P": "複数人シーン",
        "調教": "強めの展開",
        "首絞め": "強めの展開",
        "レイプ": "強制系",
        "凌辱": "強制系",
        "痴漢": "接触系",
        "痴女": "積極的な女性",
        "盗撮": "ドキュメント風",
        "のぞき": "ドキュメント風",
        "露出": "屋外系",
        "野外": "屋外系",
        "不倫": "背徳系",
        "NTR": "背徳系",
        "人妻": "既婚女性",
        "熟女": "大人女性",
    }

    for before, after in replacements.items():
        text = text.replace(before, after)

    return text

def sanitize_obj(obj):
    if isinstance(obj, dict):
        return {k: sanitize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_obj(v) for v in obj]
    if isinstance(obj, str):
        return sanitize_text(obj)
    return obj

current_theme = load_json("current_theme.json")
works = load_json("selected_article_works.json")
reviews = load_json("reviews.json")

safe_theme = sanitize_obj(current_theme)
safe_works = sanitize_obj(works)
safe_reviews = sanitize_obj(reviews)

prompt = f"""
あなたは成人向けアフィリエイトブログのSEO編集者です。

以下のテーマ・作品データ・レビュー傾向をもとに、
WordPressにそのまま貼れる記事本文を作成してください。

【重要】
入力データ内の一部表現は安全化のため置換されています。
記事では露骨な行為描写を新規生成せず、作品の特徴・比較・向き不向きを中心に整理してください。

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

【文体ガイド】
・導入文では、読者が「どれを選べばいいか迷っている」状態から始める
・仕事終わり、疲れた夜、スマホで作品を探している読者を想定する
・ジャンル名を出し、そのジャンルの中でも作品ごとに違いがあることを説明する
・「今回はその違いを比較しながら選べるように整理する」という流れにする
・各作品紹介では、最初に「この作品は〇〇を楽しみたい人向け」と結論を書く
・その後、メーカー、ジャンル、評価、レビュー傾向、タグから特徴を整理する
・おすすめポイントは3つ
・気になるポイントは2つ
・こんな人におすすめは3つ
・最後に比較表を置き、作品ごとの違いを一目で分かるようにする
・総評では「迷ったらどれを選ぶべきか」を2〜3本に絞って提案する
・関連記事はURLを作らず、関連テーマ案を3つ出す
・冷静な比較解説を基本にする
・少し熱量はあるが、煽りすぎない
・判断軸は「選びやすさ」「没入感」「リアル感」「背徳感」「疑似恋愛感」を使う

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

<!-- wp:table {{"className":"review-table"}} -->
<figure class="wp-block-table review-table"><table class="has-fixed-layout"><thead><tr><th>作品</th><th>特徴</th><th>おすすめ度</th></tr></thead><tbody>
<tr><td>作品名</td><td>特徴</td><td>★★★★★<br>おすすめ理由</td></tr>
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading -->
<h2 class="wp-block-heading">【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>
<!-- /wp:heading -->

<!-- wp:heading -->
<h2 class="wp-block-heading">関連記事</h2>
<!-- /wp:heading -->

関連記事は、現時点ではURLを作らず、関連テーマ案を3件だけ出力する。

【テーマ】
{json.dumps(safe_theme, ensure_ascii=False, indent=2)}

【作品データ】
{json.dumps(safe_works, ensure_ascii=False, indent=2)}

【レビュー情報】
{json.dumps(safe_reviews, ensure_ascii=False, indent=2)}
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

output_path = DATA_DIR / "generated_article.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(article)

print("記事生成完了")
print(f"article_path={output_path}")
