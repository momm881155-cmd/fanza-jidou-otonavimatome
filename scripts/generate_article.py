import os
import json
import re
import time
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
        "人妻": ["既婚女性"],
        "熟女": ["大人女性"],
        "巨乳": ["グラマラスなスタイル"],
        "爆乳": ["圧倒的なスタイル"],
        "巨尻": ["メリハリのあるスタイル"],

        "アダルト": ["A⚫︎作品"],
        "エロ": ["エ⚫︎"],
        "エッチ": ["エ⚫︎チ"],

        "セックス": ["本番シーン"],
        "SEX": ["本番シーン"],

        "中出し": ["フィニッシュ"],
        "生中出し": ["生フィニッシュ"],
        "フェラ": ["サービスシーン"],
        "顔射": ["フィニッシュ演出"],
        "射精": ["フィニッシュ"],
        "精子": ["フィニッシュ演出"],
        "ザーメン": ["フィニッシュ演出"],

        "挿入": ["本番シーン"],
        "喘ぎ": ["リアクション"],
        "潮吹き": ["鯨級の見せ場"],

        "ハメ撮り": ["主観演出"],

        "NTR": ["N⚫︎R"],
        "不倫": ["背徳系"],

        "痴女": ["肉食系女子"],

        "盗撮": ["観察系"],
        "のぞき": ["観察視点の演出"],

        "露出": ["開放系"],
        "野外": ["アウトドア系"],

        "風俗": ["お店系"],
        "ラブホ": ["休憩スポット"],

        "調教": ["育成系"],
        "レイプ": ["強制系"],
        "凌辱": ["ハードタイプ"],
        "痴漢": ["接触系"],

        "ドM": ["受けタイプ"],
        "ドS": ["攻めタイプ"]
    }

    for before in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(before, replacements[before][0])

    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()



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
    if not isinstance(genres, list):
        genres = []

    safe_genres = []
    for g in genres:
        if g is None:
            continue
        g = str(g).strip()
        if g:
            safe_genres.append(g)

    theme_genre = "" if theme_genre is None else str(theme_genre).strip()

    joined = " ".join(safe_genres + [theme_genre])
    
    if "大人女性" in joined or "既婚女性" in joined:
        return "落ち着いた雰囲気、生活感、説得力"
    if "主観系" in joined or "ドキュメント風" in joined:
        return "距離感の近さ、臨場感、自然な流れ"
    if "グラマラス" in joined:
        return "見た目のインパクト、視覚的な満足感"
    if "非日常系" in joined:
        return "関係性のスリル、展開力、シチュエーション性"
    if "単体作品" in joined:
        return "出演者の魅力、作品全体のまとまり"
    if "素人" in joined:
        return "自然な雰囲気、親近感、素朴さ"

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


def fix_markdown_artifacts(article):
    article = article.replace("＊＊", "**")

    article = re.sub(
        r'\*\*(.+?)\*\*',
        r'<strong><span class="bold-red">\1</span></strong>',
        article
    )

    article = re.sub(r'^\s*#{1,6}\s*(.+)$', r'\1', article, flags=re.MULTILINE)

    article = re.sub(
        r'(?m)^\s*\d+\.\s+(.+)$',
        r'<!-- wp:paragraph -->\n<p>\1</p>\n<!-- /wp:paragraph -->',
        article
    )

    article = re.sub(r'(?m)^\s*[-*]\s+(.+)$', r'<li>\1</li>', article)

    return article


def fix_bold_red(article):
    for _ in range(5):
        article = article.replace('<span class="bold-red"><span class="bold-red">', '<span class="bold-red">')
        article = article.replace('</span></span></strong>', '</span></strong>')

    article = re.sub(
        r'「<strong>(?!<span class="bold-red">)(.*?)</strong>」',
        r'「<strong><span class="bold-red">\1</span></strong>」',
        article
    )

    return article


def style_section_lists(article):
    styles = {
        "おすすめポイント": "icon-list-circle",
        "気になるポイント": "icon-list-cross",
        "こんな人におすすめ": "icon-list-thumb-up",
    }

    for heading, style_class in styles.items():

        pattern = (
            r'(<h4[^>]*>\s*'
            + re.escape(heading)
            + r'\s*</h4>\s*'
            r'<!--\s*/wp:heading\s*-->\s*)'
            r'<!--\s*wp:list(?:\s+\{.*?\})?\s*-->\s*'
            r'<ul(?:\s+class="[^"]*")?>'
        )

        replacement = (
            r'\1'
            f'<!-- wp:list {{"extraBorder":"blank-box-blue","extraStyle":"{style_class}"}} -->\n'
            f'<ul class="wp-block-list is-style-blank-box-blue has-border is-style-{style_class} has-list-style">'
        )

        article = re.sub(
            pattern,
            replacement,
            article,
            flags=re.DOTALL
        )

    return article

def remove_article_images(article):
    article = re.sub(
        r'<!-- wp:image[\s\S]*?<!-- /wp:image -->\s*',
        '',
        article
    )
    article = re.sub(
        r'<figure class="wp-block-image[\s\S]*?</figure>\s*',
        '',
        article
    )
    return article


def validate_article_structure(article, works_count):
    table_pos = article.find("【比較】今回紹介したおすすめ作品")
    summary_pos = article.find("【まとめ】迷ったらまずは比較表から選ぶのがおすすめ")

    if table_pos == -1:
        raise Exception("比較表見出しがありません")

    if summary_pos == -1:
        raise Exception("まとめ見出しがありません")

    if summary_pos < table_pos:
        raise Exception("まとめが比較表より前に出ています")

    return True


def post_process_article(article, internal_works, theme_name):

    article = fix_markdown_artifacts(article)
    article = remove_article_images(article)

    article = re.sub(
        r'<!-- wp:paragraph -->\s*<p><a href="https://github\.com/[^"]*"></a></p>\s*<!-- /wp:paragraph -->',
        '',
        article
    )

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
    article = re.sub(
        r'<!-- wp:paragraph -->\s*<p>(\[fanza_button[^\]]+\])</p>\s*<!-- /wp:paragraph -->',
        r'<!-- wp:shortcode -->\n\1\n<!-- /wp:shortcode -->',
        article
    )

    article = article.replace(
        '<!-- wp:list -->\n<ul class="wp-block-list">',
        '<!-- wp:list {"extraBorder":"blank-box-blue","extraStyle":"icon-list-circle"} -->\n<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-circle has-list-style">'
    )

    article = re.sub(
        r'<!-- wp:list \{"className":"wp-block-list"\} -->\s*<ul class="wp-block-list">',
        '<!-- wp:list {"extraBorder":"blank-box-blue","extraStyle":"icon-list-circle"} -->\n<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-circle has-list-style">',
        article
    )

    article = style_section_lists(article)

    article = article.replace(
        '<!-- wp:table -->\n<figure class="wp-block-table">',
        '<!-- wp:table {"className":"review-table"} -->\n<figure class="wp-block-table review-table">'
    )

    article = fix_bold_red(article)

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
・レビューが無い時に、レビュー数は少ないまたはレビュー数が無いなどの文言は1記事一回までしか使用しない
・レビューは評価傾向として要約する
・作品情報の羅列ではなく、比較・判断・向き不向きを重視する
・具体的すぎる描写は新規生成しない
・記事本文内にアイキャッチ画像、メイン画像、サンプル画像を挿入しない
・画像はWordPressのfeatured_mediaで設定する前提とする

【出力禁止ルール】
以下のMarkdown記法は禁止。
・#
・##
・###
・####
・*
・**
・***
・1.
・2.
・3.
・- 
・Markdownリンク

必ずWordPressブロックHTMLのみで出力すること。
番号付きリストは禁止。
Markdownの太字は禁止。
作品紹介本文では「作品01」「作品02」「作品09」などの作品番号表記は禁止。
作品番号や順位を主語にしない。
作品を指す場合は、
「本作は」
「本作の魅力は」
「本作最大の特徴は」
「特に評価したいのは」
「まず注目したいのは」
「魅力として挙げられるのは」
など自然な表現を使う。
・「本作は〜です」を連発しない
・「本作は」の使用は記事内で最大2回まで
・作品紹介の書き出しは毎回変える
・「作品01は」「1位の作品は」のような機械的な書き出しは禁止
比較表やまとめで作品リンクを出す場合は、必ず [WORK_LINK_番号] を使う。

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
28〜45文字程度。
検索キーワードを自然に含める。
AVおすすめ◯選を入れる。
サブタイトルはテーマごとに変える。
毎回同じ文言を使わない。

【人間味ある文体ルール】
・導入文は、読者が夜にスマホで作品を探している場面から自然に入る
・読者に話しかけるように書くが、煽りすぎない
・説明文だけで終わらず、「なぜこの作品を選ぶ価値があるのか」を添える
・各作品の本文は、最初に結論、その後に特徴、最後に向き不向きを自然に入れる
・ロボットっぽい定型文を避ける
・「本作は〜です」「〜と言えるでしょう」を連発しない
・作品ごとに appeal_axis、review_trend_hint、genres を使って差を出す
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

【構成崩れ防止ルール】
・記事は必ず以下の順番で出力する
・導入文
・このテーマの作品が人気な理由
・失敗しない選び方
・編集部の選定基準
・素人×テーマ名おすすめ作品一覧
・作品紹介01〜10
・比較表
・まとめ
・関連記事

・作品紹介は必ず [WORK_HEADING_01] から [WORK_HEADING_10] まで番号順に連続して出力する
・作品紹介の途中に比較表、まとめ、関連記事を入れてはいけない
・比較表より後に作品紹介を書いてはいけない
・まとめより後に作品紹介を書いてはいけない
・関連記事は記事の最後にだけ出力する
・各作品で [WORK_HEADING_番号]、[WORK_ITEM_番号]、[WORK_BUTTON_番号] は必ず1回だけ使う
・同じ作品プレースホルダーを2回以上使ってはいけない

【記事構成】
導入文 400〜500字

<!-- wp:heading -->
<h2 class="wp-block-heading">このテーマの作品が人気な理由</h2>
<!-- /wp:heading -->

テーマ特有の魅力や人気の理由を解説する。400〜500字

<!-- wp:heading -->
<h2 class="wp-block-heading">失敗しない選び方</h2>
<!-- /wp:heading -->

初めて見る人にも分かるように、選び方を解説する。

<!-- wp:heading -->
<h2 class="wp-block-heading">編集部の選定基準</h2>
<!-- /wp:heading -->

選定基準は番号付きリストにしない。
必ず以下の形式で出力する。

<!-- wp:list {{"extraBorder":"blank-box-blue","extraStyle":"icon-list-circle"}} -->
<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-circle has-list-style">
<li>選定基準を1つ説明する</li>
<li>選定基準を1つ説明する</li>
<li>選定基準を1つ説明する</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {{"textAlign":"center"}} -->
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
<figure class="wp-block-table review-table"><table class="has-fixed-layout"><thead><tr><th>作品</th><th>向いている人</th><th>特徴</th><th>おすすめ度</th></tr></thead><tbody>
<tr><td>[WORK_LINK_01]</td><td>向いている人</td><td>特徴</td><td>★★★★★<br>おすすめ理由</td></tr>
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading -->
<h2 class="wp-block-heading">【まとめ】迷ったらまずは比較表から選ぶのがおすすめ</h2>
<!-- /wp:heading -->

まとめ本文で作品名を出す場合は [WORK_LINK_番号] を使う。

【まとめルール】
まとめは3段落以内。
紹介作品を再度すべて解説しない。
作品リンクは最大3作品まで。
初心者向け・テーマ重視向け・刺激重視向けの3カテゴリに整理して簡潔に紹介する。
1カテゴリにつき1作品のみ紹介する。
まとめ全体は400文字以内にする。
Markdownの太字や番号付きリストは使わない。

【関連記事ルール】
既存記事履歴にURL付き記事がある場合のみ、今回テーマと近いものを最大3件選んで関連記事として出力する。

関連記事見出しは以下にする。

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">あわせて読みたい記事</h3>
<!-- /wp:heading -->

関連記事はul/li形式で出力する。
URLがない記事、存在しないURL、架空URLは絶対に作らない。
既存記事履歴に使えるURLがない場合は、関連記事本文は出力しない。
related_theme_candidates も出力しない。

【テーマ】
{safe_theme}

【記事用作品データ】
{json.dumps(prompt_items, ensure_ascii=False, indent=2)}

【既存記事履歴】
{json.dumps(history_items, ensure_ascii=False, indent=2)}

【SEO差別化ルール】
作品紹介だけの記事にしないこと。
作品紹介に入る前に、このテーマが人気な理由、選び方、比較ポイントを解説すること。

各作品で異なる評価軸を最低2つ使用すること。
同じ評価軸を連続使用しないこと。
同一記事内で同じ評価軸の使用回数は3回までにすること。
「リアル感」「没入感」「非日常感」「感情変化」「クライマックス」の繰り返しを避けること。

使用できる評価軸例：
完成度、満足度、見やすさ、テンポ、構成力、安定感、情報量、まとまり、リピートしやすさ、出演者の魅力、自然さ、存在感、親近感、表情の豊かさ、雰囲気、個性、距離感、キャラクター性、生活感、説得力、自然な流れ、ドキュメント感、空気感、臨場感、偶発性、素朴さ、企画性、独自性、発想の面白さ、ルール設定、ゲーム性、検証要素、展開の分かりやすさ、見せ場までの導線、物語性、関係性、展開力、ドラマ性、感情移入しやすさ、シチュエーション性、入りやすさ、クセの少なさ、万人向け、ジャンル入門向け、見疲れしにくさ、選びやすさ、分かりやすさ、ジャンル特化度、テーマ再現度、属性の強さ、ビジュアル面の満足度、設定の分かりやすさ、好みとの一致度、評価の安定感、レビュー人気、話題性、評価点とのバランス、レビュー件数との信頼感
"""

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

validate_article_structure(article, len(internal_works))

article = post_process_article(article, internal_works, theme_name)
output_path = DATA_DIR / "generated_article.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(article)

print("記事生成完了")
print(f"article_path={output_path}")
