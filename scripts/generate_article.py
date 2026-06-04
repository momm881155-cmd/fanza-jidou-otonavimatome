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
        "AV": "映像作品",
        "av": "映像作品",
        "アダルト": "作品",
        "エロ": "魅力",
        "エッチ": "親密さ",
        "セックス": "距離感の近い場面",
        "SEX": "距離感の近い場面",
        "中出し": "終盤の見せ場",
        "生中出し": "終盤の見せ場",
        "生ハメ": "距離感の近い場面",
        "ハメ撮り": "主観系",
        "フェラ": "見せ場",
        "奉仕": "丁寧な見せ場",
        "顔射": "終盤の演出",
        "射精": "終盤の演出",
        "精子": "終盤の演出",
        "ザーメン": "終盤の演出",
        "ごっくん": "印象的な見せ場",
        "チンポ": "テーマ要素",
        "チ●ポ": "テーマ要素",
        "チ〇ポ": "テーマ要素",
        "デカチン": "テーマ要素",
        "デカマラ": "テーマ要素",
        "ペニス": "テーマ要素",
        "勃起": "テーマ要素",
        "オマ○コ": "テーマ要素",
        "マ〇コ": "テーマ要素",
        "挿入": "見せ場",
        "ピストン": "動きのある場面",
        "イキ": "リアクション",
        "イク": "リアクション",
        "喘ぎ": "リアクション",
        "快感": "見せ場",
        "性欲": "テーマ性",
        "性": "テーマ",
        "裸": "身体表現",
        "肉体": "スタイル",
        "おっぱい": "スタイル",
        "乳": "スタイル",
        "尻": "スタイル",
        "爆乳": "グラマラス",
        "巨乳": "グラマラス",
        "巨尻": "グラマラス",
        "キツマン": "テーマ要素",
        "潮吹き": "リアクション",
        "3P": "複数人展開",
        "4P": "複数人展開",
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
        "ラブホ": "室内シーン",
        "風俗": "非日常系",
        "不倫": "非日常系",
        "NTR": "非日常系",
        "人妻": "既婚女性",
        "熟女": "大人女性",
        "ドスケベ": "積極的",
        "ヤリマン": "積極的",
        "ヤリ": "積極的",
        "便女": "積極的",
        "発情": "積極的",
        "変態": "個性派",
        "童貞": "初心者設定",
        "早漏": "短時間設定",
        "ドピュ": "終盤の演出",
        "ドチャシコ": "強め",
        "しゃぶ": "見せ場",
        "バキューム": "見せ場",
        "イラマ": "強めの見せ場",
        "ドM": "受け身寄り",
        "ドＳ": "主導的",
        "ドS": "主導的",
        "甘サド": "主導的",
    }

    for before, after in replacements.items():
        text = text.replace(before, after)

    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def safe_list(values, limit=8):
    if not isinstance(values, list):
        return []
    result = []
    for v in values[:limit]:
        s = sanitize_text(v)
        if s:
            result.append(s)
    return result

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
    if "非日常系" in joined:
        return "非日常感、関係性のスリル、没入感"
    if "単体作品" in joined:
        return "出演者の魅力、作品全体のまとまり"
    if "素人" in joined:
        return "自然な雰囲気、親近感、リアル感"

    return "ジャンルとの相性、見やすさ、総合バランス"

def build_review_hint(raw_texts):
    safe_texts = []
    for t in raw_texts[:4]:
        s = sanitize_text(t)
        if s:
            safe_texts.append(s[:120])

    if not safe_texts:
        return "レビュー本文は少なめ。評価点、レビュー件数、ジャンル、メーカー情報から特徴を整理する。"

    return " / ".join(safe_texts[:3])

def build_article_works(works, reviews):
    internal = []
    prompt_items = []

    if not isinstance(works, list):
        return internal, prompt_items

    for idx, w in enumerate(works, start=1):
        if not isinstance(w, dict):
            continue

        cid = w.get("content_id") or ""
        raw_title = w.get("title") or f"作品{idx:02d}"
        safe_title = sanitize_text(raw_title)
        genres = safe_list(w.get("genres", []), limit=10)
        theme_genre = sanitize_text(w.get("theme_genre") or "")
        review_texts = collect_review_texts(cid, reviews)
        number = f"{idx:02d}"

        full = {
            "rank": idx,
            "number": number,
            "content_id": cid,
            "title": raw_title,
            "safe_title": safe_title,
            "url": w.get("url") or "",
            "image": w.get("image") or "",
            "maker": sanitize_text(w.get("maker")),
            "rating": w.get("review_average"),
            "review_count": w.get("review_count"),
            "score": w.get("score"),
            "theme_genre": theme_genre,
            "genres": genres,
        }
        internal.append(full)

        prompt_items.append({
            "rank": idx,
            "number": number,
            "work_key": f"WORK_{number}",
            "safe_title": f"作品{number}",
            "maker": full["maker"],
            "rating": full["rating"],
            "review_count": full["review_count"],
            "score": full["score"],
            "theme_genre": theme_genre,
            "genres": genres,
            "appeal_axis": infer_axis(genres, theme_genre),
            "description_hint": "テーマに関連する特徴を持つ作品。ジャンル傾向と評価情報から特徴を整理する。",
            "review_trend_hint": build_review_hint(review_texts),
            "review_trend_hint": "レビューでは作品全体の雰囲気や見やすさに関する評価が見られる。",
            "heading_placeholder": f"[WORK_HEADING_{number}]",
            "item_placeholder": f"[WORK_ITEM_{number}]",
            "button_placeholder": f"[WORK_BUTTON_{number}]",
            "link_placeholder": f"[WORK_LINK_{number}]",
        })

    return internal, prompt_items

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

def guess_theme_name(current_theme, prompt_items):
    if isinstance(current_theme, dict):
        for key in ("theme", "theme_name", "name", "genre", "keyword"):
            if current_theme.get(key):
                value = sanitize_text(current_theme.get(key))
                if value:
                    return value[:30]

    if prompt_items:
        tg = prompt_items[0].get("theme_genre") or ""
        if tg:
            return tg[:30]

    return "注目"

def build_default_title(theme_name, count):
    return f"素人×{theme_name}おすすめ{count}選｜比較して選べる注目作品まとめ"

def shortcode_heading(number, title):
    safe = str(title or "").replace('"', '&quot;')
    return f'<!-- wp:shortcode -->\n[fanza_heading number="{number}" title="{safe}"]\n<!-- /wp:shortcode -->'

def shortcode_item(cid):
    return f'<!-- wp:shortcode -->\n[fanza_item cid="{cid}"]\n<!-- /wp:shortcode -->'

def shortcode_button(url):
    return f'<!-- wp:shortcode -->\n[fanza_button url="{url}" text="動画を見る"]\n<!-- /wp:shortcode -->'

def post_process_article(article, internal_works, theme_name):
    # GitHubの空アンカー削除
    article = re.sub(
        r'<!-- wp:paragraph -->\s*<p><a href="https://github\.com/[^"]*"></a></p>\s*<!-- /wp:paragraph -->',
        '',
        article
    )

    # プレースホルダーを正規ショートコードへ
    for w in internal_works:
        number = w["number"]
        title = w.get("title") or w.get("safe_title") or f"作品{number}"
        cid = w.get("content_id") or ""
        url = w.get("url") or "#"

        article = article.replace(f"[WORK_HEADING_{number}]", shortcode_heading(number, title))
        article = article.replace(f"[WORK_ITEM_{number}]", shortcode_item(cid))
        article = article.replace(f"[WORK_BUTTON_{number}]", shortcode_button(url))
        article = article.replace(
            f"[WORK_LINK_{number}]",
            f'<a href="{url}" target="_blank" rel="nofollow sponsored noopener">{str(title).replace(chr(34), "&quot;")}</a>'
        )

    # 段落化されたショートコードを戻す
    article = re.sub(
        r'<!-- wp:paragraph -->\s*<p>(\[fanza_heading[^\]]+\])</p>\s*<!-- /wp:paragraph -->',
        r'<!-- wp:shortcode -->\n\1\n<!-- /wp:shortcode -->',
        article
    )
    article = re.sub(
        r'<!-- wp:paragraph -->\s*<p>(\[fanza_item[^\]]+\])</p>\s*<!-- /wp:paragraph -->',
        r'<!-- wp:shortcode -->\n\1\n<!-- /wp:shortcode -->',
        article
    )

    # 壊れたfanza_buttonを、作品順に正しいURLで補正
    for w in internal_works:
        url = w.get("url") or "#"
        correct = shortcode_button(url)
        article = re.sub(
            r'<!-- wp:paragraph -->\s*<p>\[fanza_button url=".*?" text="動画を見る"\]</p>\s*<!-- /wp:paragraph -->',
            correct,
            article,
            count=1,
            flags=re.DOTALL,
        )

    # 通常リストを最低限青囲みに補正
    article = article.replace(
        '<!-- wp:list -->\n<ul class="wp-block-list">',
        '<!-- wp:list {"extraBorder":"blank-box-blue","extraStyle":"icon-list-circle"} -->\n<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-circle has-list-style">'
    )

    # 比較表にreview-tableを付与
    article = article.replace(
        '<!-- wp:table -->\n<figure class="wp-block-table">',
        '<!-- wp:table {"className":"review-table"} -->\n<figure class="wp-block-table review-table">'
    )

    # 赤太字
    article = re.sub(
        r'「<strong>(.*?)</strong>」',
        r'「<strong><span class="bold-red">\1</span></strong>」',
        article
    )

    # title / eye_catch がなければ付与
    if "<!-- title:" not in article:
        article = f"<!-- title: {build_default_title(theme_name, len(internal_works))} -->\n" + article

    if "<!-- eye_catch_image:" not in article:
        image_work = next((w for w in internal_works if w.get("image")), None)
        if image_work:
            article = (
                f'<!-- eye_catch_image: {image_work.get("image")} -->\n'
                f'<!-- eye_catch_source: {sanitize_text(image_work.get("title"))} -->\n'
                + article
            )

    # 手動投稿でも画像が見えるように画像ブロックを冒頭に入れる
    if "<!-- wp:image" not in article:
        image_work = next((w for w in internal_works if w.get("image")), None)
        if image_work:
            img = image_work.get("image")
            alt = sanitize_text(image_work.get("title"))
            image_block = (
                '<!-- wp:image {"sizeSlug":"large"} -->\n'
                f'<figure class="wp-block-image size-large"><img src="{img}" alt="{alt}"/></figure>\n'
                '<!-- /wp:image -->\n'
            )
            pos = article.find("<!-- wp:paragraph -->")
            if pos != -1:
                article = article[:pos] + image_block + article[pos:]
            else:
                article = image_block + article

    return article

current_theme = load_json("current_theme.json", {})
works = load_json("selected_article_works.json", [])
reviews = load_json("reviews.json", {})
article_history = load_json("article_history.json", [])

internal_works, prompt_items = build_article_works(works, reviews)
history_items = normalize_history_items(article_history)
theme_name = guess_theme_name(current_theme, prompt_items)
safe_theme = sanitize_text(json.dumps(current_theme, ensure_ascii=False))

prompt = f"""
あなたは映像作品紹介ブログのSEO編集者です。

以下のテーマ・記事用作品データ・既存記事履歴をもとに、WordPressにそのまま貼れる記事本文を作成してください。

【重要】
入力データは安全化されています。具体的すぎる描写を増やさず、作品の特徴・比較・向き不向き・レビュー傾向を整理してください。

【最重要ルール】
・出力は記事本文のみ
・前置きや説明は不要
・WordPressのコードエディターに貼れる形式で出力する
・本文内に<h1>は使わない
・h2/h3/h4タグを使う
・作品ごとに同じ言い回しを繰り返さない
・レビュー本文の直接引用は禁止
・レビューは評価傾向として要約する
・作品情報の羅列ではなく、比較・判断・向き不向きを重視する
・具体的すぎる描写は新規生成しない

【プレースホルダールール】
作品見出し、作品情報、作品ボタン、作品リンクは必ず以下のプレースホルダーを使う。
URLやショートコードを自分で作らない。

作品冒頭：
[WORK_HEADING_01]
[WORK_ITEM_01]

作品末尾：
[WORK_BUTTON_01]

比較表やまとめ内の作品リンク：
[WORK_LINK_01]

2位以降も、02、03、04のように作品データのnumberに合わせる。

【タイトル・アイキャッチルール】

本文の最初に必ず以下を出力する。

<!-- title: SEOタイトル -->

SEOタイトルは必ずテーマに合わせて毎回考えること。

タイトル形式例

素人×奉仕おすすめ10選｜献身的な距離感を楽しめる人気作品まとめ

素人×恋人感おすすめ7選｜リアルな関係性を味わえる注目作品まとめ

素人×巨乳おすすめ10選｜満足度の高い人気作品を厳選紹介

ルール

・28〜45文字程度
・検索キーワードを自然に含める
・おすすめ◯選を入れる
・サブタイトルはテーマごとに変える
・毎回同じ文言を使わない
・クリックしたくなる自然なタイトルにする

【人間味ある文体ルール】
・導入文は、読者が夜にスマホで作品を探している場面から自然に入る
・読者に話しかけるように書くが、煽りすぎない
・説明文だけで終わらず、「なぜこの作品を選ぶ価値があるのか」を添える
・各作品の本文は、最初に結論、その後に特徴、最後に向き不向きを自然に入れる
・ロボットっぽい定型文を避ける
・「本作は〜です」「〜と言えるでしょう」を連発しない
・作品ごとに appeal_axis、review_trend_hint、genres を使って差を出す
・判断軸は「選びやすさ」「没入感」「リアル感」「非日常感」「疑似恋愛感」を使う
・文章は冷静な比較解説を基本にしつつ、少しだけ熱量を出す

【強調ルール】
重要な「」内のフレーズは以下の形式にする。

「<strong><span class="bold-red">強調したい文章</span></strong>」

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
導入文 400〜700字

<!-- wp:heading -->
<h2 class="wp-block-heading">このテーマの作品が人気な理由</h2>
<!-- /wp:heading -->

テーマ特有の魅力や人気の理由を解説する。

<!-- wp:heading -->
<h2 class="wp-block-heading">失敗しない選び方</h2>
<!-- /wp:heading -->

始めてみる人に選び方を解説する。

<!-- wp:heading -->
<h2 class="wp-block-heading">編集部の選定基準</h2>
<!-- /wp:heading -->

今回のランキングで重視したポイントを説明する。

<!-- wp:heading {"textAlign":"center"} -->
<h2 class="wp-block-heading has-text-align-center">素人×{theme_name}おすすめ作品一覧</h2>
<!-- /wp:heading -->
各作品をランキング順に紹介する。

作品ごとに以下を必ず入れる。
1. [WORK_HEADING_番号]
2. [WORK_ITEM_番号]
3. 作品紹介本文 2〜4段落
作品紹介本文は必ず以下の順番で書く。
1段落目：この作品がランクインした理由
2段落目：同テーマ内での強み・他作品との違い
3段落目：向いている人・向いていない人
4. おすすめポイント
5. 気になるポイント
6. こんな人におすすめ
7. [WORK_BUTTON_番号]
8. 区切り線

<!-- wp:heading -->
<h2 class="wp-block-heading">【比較】今回紹介したおすすめ作品</h2>
<!-- /wp:heading -->

比較表の作品名には [WORK_LINK_番号] を使う。

<!-- wp:table {{"className":"review-table"}} -->
<figure class="wp-block-table review-table"><table class="has-fixed-layout"><thead><tr><th>作品</th><th>特徴</th><th>おすすめ度</th></tr></thead><tbody>
<tr><td>[WORK_LINK_01]</td><td>特徴</td><td>★★★★★<br>おすすめ理由</td></tr>
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading -->
<h2 class="wp-block-heading">【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>
<!-- /wp:heading -->

まとめ本文で作品名を出す場合は [WORK_LINK_番号] を使う。
総評では、今回のテーマでどんな人がどの作品を選ぶべきかを整理する。
特におすすめの作品を2〜3本挙げて、選ぶ理由を説明する。

【関連記事ルール】
既存記事履歴にURL付き記事がある場合のみ、今回テーマと近いものを最大3件選んで関連記事として出力する。
URLがない記事、存在しないURL、架空URLは絶対に作らない。
既存記事履歴に使えるURLがない場合は、関連記事本文は出力せず、related_theme_candidates のみ出力する。

【テーマ】
{safe_theme}

【記事用作品データ】
{json.dumps(prompt_items, ensure_ascii=False, indent=2)}

【既存記事履歴】
{json.dumps(history_items, ensure_ascii=False, indent=2)}
"""
【SEO差別化ルール】

作品紹介だけの記事にしないこと。

作品紹介に入る前に、

・このテーマが人気な理由
・選び方
・比較ポイント

を解説すること。

各作品で異なる評価軸を使用すること。

使用できる評価軸例

【完成度】
完成度
満足度
見やすさ
テンポ
安定感

【出演者】
出演者の魅力
自然さ
存在感
親近感
雰囲気

【リアリティ】
リアルさ
生活感
説得力
没入しやすさ

【企画】
企画性
独自性
発想
ゲーム性

【ストーリー】
関係性
ドラマ性
感情移入

【初心者向け】
入りやすさ
クセの少なさ
万人向け

【レビュー】
評価の安定感
レビュー人気
話題性

各作品で異なる評価軸を最低2つ使用すること。

同じ評価軸を連続使用しないこと。

「リアル感」「没入感」「非日常感」の繰り返しを避けること。

import time

response = None
last_error = None

for attempt in range(5):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        break
    except Exception as e:
        last_error = e
        print(f"Gemini error attempt {attempt + 1}/5: {e}")
        time.sleep(10 * (attempt + 1))

if response is None:
    raise last_error

print("===== GEMINI RESPONSE =====")
print(response)

if response is None:
    raise Exception("Gemini returned None")

if not getattr(response, "text", None):
    raise Exception(f"Gemini returned no text: {response}")

article = response.text.strip()

if not article:
    raise Exception("Gemini returned empty article")

article = post_process_article(article, internal_works, theme_name)

output_path = DATA_DIR / "generated_article.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(article)

print("記事生成完了")
print(f"article_path={output_path}")
