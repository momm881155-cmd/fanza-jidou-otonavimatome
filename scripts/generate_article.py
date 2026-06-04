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

def load_json(name, default=None):
    path = DATA_DIR / name
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def sanitize_text(text):
    if text is None:
        return ""

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
        "爆乳": "グラマラス",
        "巨乳": "グラマラス",
        "ハメ撮り": "主観系",
        "オナニー": "ソロシーン",
        "3P": "複数人シーン",
        "4P": "複数人シーン",
        "調教": "強めの展開",
        "首絞め": "強めの展開",
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
        "レイプ": "強制系",
        "凌辱": "強制系",
    }

    for before, after in replacements.items():
        text = text.replace(before, after)

    text = re.sub(r"\s+", " ", text).strip()
    return text

def safe_list(values, limit=8):
    if not isinstance(values, list):
        return []
    return [sanitize_text(v) for v in values[:limit] if sanitize_text(v)]

def collect_review_texts(content_id, reviews):
    texts = []

    if isinstance(reviews, dict):
        possible = reviews.get(content_id, [])
        if isinstance(possible, dict):
            possible = [possible]
        if isinstance(possible, list):
            for r in possible:
                if isinstance(r, dict):
                    t = r.get("text") or r.get("review") or r.get("content") or r.get("comment") or ""
                else:
                    t = str(r)
                if t:
                    texts.append(t)

    elif isinstance(reviews, list):
        for r in reviews:
            if not isinstance(r, dict):
                continue
            if r.get("content_id") != content_id:
                continue
            t = r.get("text") or r.get("review") or r.get("content") or r.get("comment") or ""
            if t:
                texts.append(t)

    return texts

def infer_axis(genres, theme_genre):
    joined = " ".join(genres + [theme_genre])

    if "大人女性" in joined or "既婚女性" in joined:
        return "落ち着いた雰囲気、生活感、リアル感"
    if "主観系" in joined or "ドキュメント風" in joined:
        return "距離感の近さ、臨場感、リアル感"
    if "グラマラス" in joined:
        return "見た目のインパクト、視覚的な満足感"
    if "背徳系" in joined:
        return "背徳感、関係性のスリル、没入感"
    if "単体作品" in joined:
        return "出演者の魅力、作品全体のまとまり"
    if "素人" in joined:
        return "自然な雰囲気、素人感、親近感"

    return "ジャンルとの相性、見やすさ、総合バランス"

def build_review_hint(raw_texts):
    safe_texts = []
    for t in raw_texts[:5]:
        t = sanitize_text(t)
        if t:
            safe_texts.append(t[:140])

    if not safe_texts:
        return "レビュー本文は少なめ。評価点、レビュー件数、ジャンル、メーカー情報から特徴を整理する。"

    return " / ".join(safe_texts)

def build_article_works(works, reviews):
    article_works = []

    if not isinstance(works, list):
        return article_works

    for idx, w in enumerate(works, start=1):
        if not isinstance(w, dict):
            continue

        cid = w.get("content_id")
        genres = safe_list(w.get("genres", []), limit=10)
        theme_genre = sanitize_text(w.get("theme_genre") or "")
        review_texts = collect_review_texts(cid, reviews)

        article_works.append({
            "rank": idx,
            "number": f"{idx:02d}",
            "content_id": cid,
            "title": sanitize_text(w.get("title")),
            "url": w.get("url"),
            "image": w.get("image"),
            "maker": sanitize_text(w.get("maker")),
            "rating": w.get("review_average"),
            "review_count": w.get("review_count"),
            "score": w.get("score"),
            "base_genre": sanitize_text(w.get("base_genre")),
            "theme_genre": theme_genre,
            "genres": genres,
            "appeal_axis": infer_axis(genres, theme_genre),
            "description_hint": f"{theme_genre or 'テーマ'}系として、{', '.join(genres[:6])} の要素がある作品。",
            "review_trend_hint": build_review_hint(review_texts),
            "comparison_note": "他作品と比べて、タグ・評価・レビュー傾向から違いが分かるように紹介する。",
        })

    return article_works

def normalize_history_items(history):
    if not history:
        return []

    if isinstance(history, dict):
        items = []
        for key in ("articles", "history", "items"):
            if isinstance(history.get(key), list):
                items = history.get(key)
                break
        if not items:
            items = list(history.values()) if all(isinstance(v, dict) for v in history.values()) else []
    elif isinstance(history, list):
        items = history
    else:
        items = []

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue

        title = item.get("title") or item.get("article_title") or item.get("theme") or ""
        url = item.get("url") or item.get("permalink") or item.get("link") or ""
        theme = item.get("theme") or item.get("theme_genre") or item.get("genre") or ""

        title = sanitize_text(title)
        theme = sanitize_text(theme)

        if title and url:
            normalized.append({
                "title": title,
                "url": url,
                "theme": theme,
            })

    return normalized[-30:]

current_theme = load_json("current_theme.json", {})
works = load_json("selected_article_works.json", [])
reviews = load_json("reviews.json", {})
article_history = load_json("article_history.json", [])

article_works = build_article_works(works, reviews)
history_items = normalize_history_items(article_history)

prompt = f"""
あなたは作品紹介ブログのSEO編集者です。

以下のテーマ・記事用作品データ・既存記事履歴をもとに、WordPressにそのまま貼れる記事本文を作成してください。

【重要】
入力データは安全化されています。具体的な行為描写を新規生成せず、作品の特徴・比較・向き不向き・レビュー傾向を整理してください。

【最重要ルール】
・出力は記事本文のみ
・前置きや説明は不要
・WordPressのコードエディターに貼れる形式で出力する
・本文内に<h1>は使わない
・h2/h3/h4タグを使う
・作品見出しは必ずショートコード [fanza_heading] を使う
・作品情報表示は必ずショートコード [fanza_item] を使う
・作品ボタンは必ずショートコード [fanza_button] を使う
・レビュー本文の直接引用は禁止
・レビューは評価傾向として要約する
・作品情報の羅列ではなく、比較・判断・向き不向きを重視する
・作品ごとに同じ言い回しを繰り返さない

【タイトル・アイキャッチルール】
本文の最初に必ず以下を出力する。

<!-- title: 素人×テーマ名おすすめ〇選｜検索意図に合うサブタイトル -->
<!-- eye_catch_image: 作品データから選んだ画像URL -->
<!-- eye_catch_source: 選んだ作品名 -->

〇選の数字は作品データの件数に合わせる。
eye_catch_image は基本的に1位作品の image を使う。
存在しない画像URLは作らない。

【人間味ある文体ルール】
・導入文は、読者が夜にスマホで作品を探している場面から自然に入る
・ただし毎回「仕事終わり」「疲れた夜」だけに寄せすぎない
・読者に話しかけるように書くが、煽りすぎない
・説明文だけで終わらず、「なぜこの作品を選ぶ価値があるのか」を一言添える
・各作品の本文は、最初に結論、その後に特徴、最後に向き不向きを自然に入れる
・ロボットっぽい定型文を避ける。繰り返しワードは1回まで。
・「本作は〜です」「〜と言えるでしょう」を連発しない
・作品ごとに appeal_axis、review_trend_hint、genres を使って差を出す
・判断軸は「選びやすさ」「没入感」「リアル感」「背徳感」「疑似恋愛感」を使う
・文章は冷静な比較解説を基本にしつつ、熱量を出す

【強調ルール】
重要な「」内のフレーズは以下の形式にする。

「<strong><span class="bold-red">強調したい文章</span></strong>」

すべての「」ではなく、重要な訴求部分だけに使う。

【ショートコードルール】
各作品の冒頭は必ず以下の形式にする。

<!-- wp:shortcode -->
[fanza_heading number="01" title="作品名"]
<!-- /wp:shortcode -->

<!-- wp:shortcode -->
[fanza_item cid="content_id"]
<!-- /wp:shortcode -->

作品紹介の最後には必ず以下を入れる。
URLは絶対に改行しない。
HTMLリンク化しない。
Markdownリンク化しない。

<!-- wp:shortcode -->
[fanza_button url="作品URL" text="動画を見る"]
<!-- /wp:shortcode -->

titleには記事用作品データの title をそのまま入れる。
cidには content_id を入れる。
urlには url を入れる。

【順位ルール】
記事用作品データの rank と number を使う。
number="01" から順番に出力する。

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
<h2 class="wp-block-heading has-text-align-center">素人×テーマ名おすすめ作品一覧</h2>
<!-- /wp:heading -->

「テーマ名」には今回のテーマから判断したテーマ名を入れる。
「テーマに合うおすすめ作品一覧」という固定文言は禁止。

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

比較表の作品名には、必ず作品データの url を使ってアフィリエイトリンクを入れる。

<!-- wp:table {{"className":"review-table"}} -->
<figure class="wp-block-table review-table"><table class="has-fixed-layout"><thead><tr><th>作品</th><th>特徴</th><th>おすすめ度</th></tr></thead><tbody>
<tr><td><a href="作品URL" target="_blank" rel="nofollow sponsored noopener">作品名</a></td><td>特徴</td><td>★★★★★<br>おすすめ理由</td></tr>
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading -->
<h2 class="wp-block-heading">【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>
<!-- /wp:heading -->

まとめ本文で作品名を出す場合は、必ず作品データの url を使ってリンクにする。
存在しないURLは作らない。
総評では、今回のテーマでどんな人がどの作品を選ぶべきかを整理する。
特におすすめの作品を2〜3本挙げて、選ぶ理由を説明する。

【関連記事ルール】
既存記事履歴にURL付き記事がある場合のみ、今回テーマと近いものを最大3件選んで関連記事として出力する。
URLがない記事、存在しないURL、架空URLは絶対に作らない。
既存記事履歴に使えるURLがない場合は、関連記事本文は出力せず、related_theme_candidates のみ出力する。

URL付き関連記事を出す場合の形式：

<!-- wp:heading -->
<h2 class="wp-block-heading">関連記事</h2>
<!-- /wp:heading -->

<ul>
<li><a href="既存記事URL">既存記事タイトル</a></li>
<li><a href="既存記事URL">既存記事タイトル</a></li>
<li><a href="既存記事URL">既存記事タイトル</a></li>
</ul>

URL付き関連記事が出せない場合の形式：

<!-- related_theme_candidates:
- 関連テーマ案1
- 関連テーマ案2
- 関連テーマ案3
-->

【テーマ】
{json.dumps(current_theme, ensure_ascii=False, indent=2)}

【記事用作品データ】
{json.dumps(article_works, ensure_ascii=False, indent=2)}

【既存記事履歴】
{json.dumps(history_items, ensure_ascii=False, indent=2)}
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
