import os
import json
import re
import time
from pathlib import Path
from google import genai
from google.genai import types


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
        # 体型・見た目
        "爆乳": ["爆桃"],
        "巨乳": ["巨桃"],
        "貧乳": ["小柄"],
        "スレンダー": ["細身"],
        "ムチムチ": ["肉感"],
        "童顔": ["童顔風"],
        "ロリ": ["童顔風"],
        "ロリ顔": ["童顔風"],

        # 属性
        "女子高生": ["制服系"],
        "女子校生": ["制服系"],
        "JK": ["制服系"],

        # 作品ジャンル
        "痴女": ["肉食女子"],
        "ドS": ["どえす"],
        "ドM": ["どえむ"],

        # 撮影
        "ハメ撮り": ["はめ鳥"],
        "個撮": ["個人撮影"],
        "自撮り": ["セルフ撮影"],
        "主観": ["主観演出"],
        "POV": ["主観演出"],

        # 場所・設定
        "ラブホ": ["ホテル"],
        "風俗": ["お店"],
        "ソープ": ["お店"],
        "デリヘル": ["お店"],
        "野外": ["屋外"],
        "露出": ["開放演出"],
        "職場": ["仕事場"],
        "学校": ["学園"],
        "自宅": ["生活感のある場所"],

        # 行為・演出は詳細化せず抽象化
        "セックス": ["ラブシーン"],
        "SEX": ["ラブシーン"],
        "挿入": ["本編の見せ場"],
        "フェラ": ["密着シーン"],
        "フェラチオ": ["密着シーン"],
        "中出し": ["終盤の演出"],
        "顔射": ["終盤の演出"],
        "射精": ["フィニッシュ"],
        "精子": ["演出"],
        "ザーメン": ["演出"],
        "手コキ": ["密着シーン"],
        "パイズリ": ["密着シーン"],
        "潮吹き": ["大きな見せ場"],
        "喘ぎ": ["リアクション"],
        "絶頂": ["盛り上がり"],
        "快感": ["高揚感"],

        # 強めの展開
        "レイプ": ["強引な展開"],
        "凌辱": ["過酷な展開"],
        "痴漢": ["接触トラブル設定"],
        "監禁": ["閉鎖空間での展開"],
        "拘束": ["拘束演出"],
        "調教": ["支配的な演出"],

        # 特殊系
        "アナル": ["特殊なプレイ"],
        "浣腸": ["特殊なプレイ"],
        "フィスト": ["特殊なプレイ"],
        "飲尿": ["特殊なプレイ"],
        "放尿": ["特殊なプレイ"],
        "スカトロ": ["特殊なプレイ"],
    }

    import random

    for old in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(old, random.choice(replacements[old]))

    return text

    for before in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(before, replacements[before][0])

    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def safe_list(values, limit=8):
    if not isinstance(values, list):
        return []

    result = []
    for v in values[:limit]:
        if v is None:
            continue
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
    for t in raw_texts[:3]:
        s = sanitize_text(t)
        if s:
            safe_texts.append(s[:60])

    if not safe_texts:
        return "レビュー本文には依存せず、評価点・ジャンル・メーカー情報・作品設定から特徴を整理する。レビュー不足を本文中の弱点として書かない。「特になし」などは書かない"

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

    return normalized[-12:]


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
    return f'<!-- wp:shortcode -->\n[fanza_heading number="{number}" title="{safe}"]\n<!-- /wp:shortcode -->\n'


def shortcode_item(cid):
    return f'<!-- wp:shortcode -->\n[fanza_item cid="{cid}"]\n<!-- /wp:shortcode -->\n'


def shortcode_button(url):
    return f'<!-- wp:shortcode -->\n[fanza_button url="{url}" text="動画を見る"]\n<!-- /wp:shortcode -->\n'


def wp_paragraph(text):
    text = sanitize_text(text)
    if not text:
        return ""
    return f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->\n'


def wp_heading(text, level=2, center=False):
    text = sanitize_text(text)
    if not text:
        return ""

    if center:
        return (
            '<!-- wp:heading {"textAlign":"center"} -->\n'
            f'<h{level} class="wp-block-heading has-text-align-center">{text}</h{level}>\n'
            '<!-- /wp:heading -->\n'
        )

    if level == 2:
        return f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{text}</h2>\n<!-- /wp:heading -->\n'

    return (
        f'<!-- wp:heading {{"level":{level}}} -->\n'
        f'<h{level} class="wp-block-heading">{text}</h{level}>\n'
        '<!-- /wp:heading -->\n'
    )


def wp_list(items, style_class="icon-list-circle"):
    if not isinstance(items, list):
        items = []

    lis = []
    for item in items:
        item = sanitize_text(item)
        if item:
            lis.append(f"<li>{item}</li>")

    if not lis:
        return ""

    return (
        '<!-- wp:html -->\n'
        f'<ul class="wp-block-list is-style-blank-box-blue has-border is-style-{style_class} has-list-style">\n'
        + "\n".join(lis) +
        '\n</ul>\n'
        '<!-- /wp:html -->\n'
    )

def wp_separator():
    return '<!-- wp:separator -->\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<!-- /wp:separator -->\n'


def clamp_list(values, min_count=0, max_count=3, fallback=""):
    if not isinstance(values, list):
        values = []
    result = [sanitize_text(v) for v in values if sanitize_text(v)]
    result = result[:max_count]
    while len(result) < min_count and fallback:
        result.append(fallback)
    return result


def get_work_label(w):
    title = sanitize_text(w.get("title"))
    if len(title) > 18:
        return title[:18] + "…"
    return title or sanitize_text(w.get("safe_title")) or "作品"


def build_compare_table(internal_works, compare_items=None):
    compare_items = compare_items if isinstance(compare_items, list) else []
    rows = []

    for idx, w in enumerate(internal_works):
        item = compare_items[idx] if idx < len(compare_items) and isinstance(compare_items[idx], dict) else {}
        url = w.get("url") or "#"
        title = get_work_label(w)

        feature = sanitize_text(item.get("feature")) or (
            "、".join(w.get("genres", [])[:2]) or sanitize_text(w.get("theme_genre")) or "特徴あり"
        )
        rating = sanitize_text(item.get("rating")) or "★★★★☆"

        if len(feature) > 20:
            feature = feature[:20] + "…"

        rows.append(
            f'<tr>'
            f'<td><a href="{url}" target="_blank" rel="nofollow sponsored noopener">{title}</a></td>'
            f'<td>{feature}</td>'
            f'<td>{rating}</td>'
            f'</tr>'
        )

    return (
        '<!-- wp:table {"className":"review-table compact-review-table"} -->\n'
        '<figure class="wp-block-table review-table compact-review-table"><table class="has-fixed-layout">'
        '<thead><tr><th>作品</th><th>特徴</th><th>評価</th></tr></thead><tbody>\n'
        + "\n".join(rows) +
        '\n</tbody></table></figure>\n<!-- /wp:table -->\n'
    )


def build_related_block(related_items):
    related_items = related_items if isinstance(related_items, list) else []
    rows = []
    for item in related_items[:3]:
        if not isinstance(item, dict):
            continue
        title = sanitize_text(item.get("title"))
        url = item.get("url") or ""
        if title and url:
            rows.append(f'<li><a href="{url}">{title}</a></li>')

    if not rows:
        return ""

    return (
    '<!-- wp:heading {"level":3} -->\n'
    '<h3 class="wp-block-heading">あわせて読みたい記事</h3>\n'
    '<!-- /wp:heading -->\n'
    '<!-- wp:html -->\n'
    '<ul class="wp-block-list is-style-blank-box-blue has-border is-style-icon-list-circle has-list-style">\n'
    + "\n".join(rows) +
    '\n</ul>\n'
    '<!-- /wp:html -->\n'
)

def extract_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise
        return json.loads(m.group(0))


def validate_json_data(data, works_count):
    if not isinstance(data, dict):
        raise Exception("Gemini JSON is not an object")

    required = ["title", "intro", "reason", "choice", "selection", "works", "summary"]
    for key in required:
        if key not in data:
            raise Exception(f"JSON key missing: {key}")

    if not isinstance(data.get("works"), list):
        raise Exception("JSON works is not a list")

    if len(data.get("works", [])) < works_count:
        raise Exception(f"JSON works count is short: {len(data.get('works', []))} < {works_count}")

    for idx, work in enumerate(data.get("works", [])[:works_count], start=1):
        if not isinstance(work, dict):
            raise Exception(f"work {idx} is not object")
        for key in ["body", "good", "bad", "recommend"]:
            if key not in work:
                raise Exception(f"work {idx} key missing: {key}")
            if not isinstance(work.get(key), list):
                raise Exception(f"work {idx} {key} is not list")

    return True


def validate_wp_blocks(article):
    blocks = [
        "paragraph",
        "heading",
        "html",
        "table",
        "separator",
        "shortcode"
    ]

    for block in blocks:
        open_count = len(
            re.findall(
                rf'<!--\s*wp:{block}(?:\s+[^>]*)?\s*-->',
                article
            )
        )

        close_count = len(
            re.findall(
                rf'<!--\s*/wp:{block}\s*-->',
                article
            )
        )

        if open_count != close_count:
            raise Exception(
                f"{block} block mismatch: open={open_count} close={close_count}"
            )

    return True

def build_article_from_json(data, internal_works, theme_name):
    article = ""

    title = sanitize_text(data.get("title") or build_default_title(theme_name, len(internal_works)))
    article += f"<!-- title: {title} -->\n"

    image_work = next((w for w in internal_works if w.get("image")), None)
    if image_work:
        article += f'<!-- eye_catch_image: {image_work.get("image")} -->\n'
        article += f'<!-- eye_catch_source: {sanitize_text(image_work.get("title"))[:80]} -->\n'

    article += wp_paragraph(data.get("intro"))

    article += wp_heading("【比較表】今回紹介するおすすめ作品")
    article += build_compare_table(internal_works, data.get("compare", []))

    article += wp_heading(f"{theme_name}おすすめ作品一覧", center=True)

    works_data = data.get("works", [])
    for i, work_text in enumerate(works_data[:len(internal_works)], start=1):
        w = internal_works[i - 1]
        number = w["number"]

        article += shortcode_heading(number, w.get("title"))
        article += shortcode_item(w.get("content_id"))

        for p in clamp_list(work_text.get("body"), min_count=3, max_count=4, fallback="ジャンルやレビュー傾向をもとに、特徴を整理して紹介します。"):
            article += wp_paragraph(p)

        article += wp_heading("おすすめポイント", 4)
        article += wp_list(clamp_list(work_text.get("good"), min_count=3, max_count=3, fallback="テーマとの相性が分かりやすい"), "icon-list-circle")

        article += wp_heading("気になるポイント", 4)
        article += wp_list(clamp_list(work_text.get("bad"), min_count=1, max_count=2, fallback="好みによって評価が分かれる可能性がある"), "icon-list-cross")

        article += wp_heading("こんな人におすすめ", 4)
        article += wp_list(clamp_list(work_text.get("recommend"), min_count=3, max_count=3, fallback="テーマ重視で選びたい方"), "icon-list-thumb-up")

        article += shortcode_button(w.get("url"))
        article += wp_separator()

    article += wp_heading("失敗しない選び方")
    article += wp_paragraph(data.get("choice"))

    article += wp_heading("このテーマの作品が人気な理由")
    article += wp_paragraph(data.get("reason"))

    article += wp_heading("【まとめ】迷ったらまずは比較表から選ぶのがおすすめ")
    for p in clamp_list(data.get("summary"), min_count=2, max_count=3, fallback="比較表を参考に、好みに合う作品から確認するのがおすすめです。"):
        article += wp_paragraph(p)

    article += build_related_block(data.get("related", []))

    validate_wp_blocks(article)
    return article


def build_prompt(current_theme, prompt_items, history_items, theme_name, works_count):
    safe_theme = sanitize_text(json.dumps(current_theme, ensure_ascii=False))

    return f"""
あなたは映像作品紹介ブログのSEO編集者です。
以下のテーマ・記事用作品データ・既存記事履歴をもとに、記事本文用のJSONだけを作成してください。

【絶対ルール】
・出力はJSONのみ
・Markdownは禁止
・WordPressブロックHTMLは禁止
・コードブロックは禁止
・説明文、前置き、補足は禁止
・JSONのキー名は指定どおりにする
・作品数は必ず {works_count} 件
・works 配列は必ず {works_count} 件出力する
・compare 配列も必ず {works_count} 件出力する
・作品紹介では作品番号や順位を主語にしない
・「作品01」「作品02」「第1位」「上位作品」などは禁止
・「本作は」「この作品は」で始める文を多用しない
・評価軸名で作品を説明しない
・完成度、満足度、テーマ再現度、ビジュアル面の満足度などの評価レポート風表現は禁止
・作品ごとの差はジャンル、設定、レビュー傾向、メーカー傾向から説明する
・抽象評価ではなく具体的な特徴で比較する
・「〜に焦点を当てた作品」「〜を表現した作品」の連続使用は禁止
・具体的すぎる描写は新規生成しない
・レビュー本文の直接引用は禁止
・レビューは傾向として要約する
・未成年を示唆する表現や違法性を強める表現は作らない
・入力にある危険な表現を増幅しない
・作品タイトルは本文に直接書かない
・レビューが少ない、レビューがない、判断しにくい等を「気になるポイント」や弱点として書かない

【文章ルール】
・introは200〜250字
・reasonは250〜350字
・choiceは250〜350字
・selectionは3件
・各works.bodyは3段落分。各段落は120〜180字程度
・各works.goodは3件
・各works.badは1〜2件
・各works.recommendは3件
・summaryは2〜3段落、合計400字以内
・煽りすぎず、冷静な比較解説にする
・compareのfeatureは20文字以内
・compareにfitやreasonは入れない
・比較表はスマホ向けに短く、1作品1行で理解できる内容にする

【JSON形式】
次の形式だけで返してください。
{{
  "title": "SEOタイトル。テーマ名、AVおすすめ、{works_count}選を自然に含める。28〜45字程度。高評価、人気、比較、厳選、初心者向けのいずれかを含める。",
  "intro": "導入文",
  "reason": "このテーマの作品が人気な理由",
  "choice": "失敗しない選び方",
  "selection": ["選定基準1", "選定基準2", "選定基準3"],
  "works": [
    {{
      "body": ["ランクイン理由", "同テーマ内での強みや違い", "向いている人・向いていない人"],
      "good": ["おすすめポイント1", "おすすめポイント2", "おすすめポイント3"],
      "bad": ["気になるポイント1"],
      "recommend": ["おすすめの人1", "おすすめの人2", "おすすめの人3"]
    }}
  ],
  "compare": [
  {{
    "feature": "20文字以内の特徴",
    "rating": "★★★★★"
  }}
],
  "summary": ["まとめ段落1", "まとめ段落2"],
  "related": [
    {{"title": "既存記事タイトル", "url": "既存記事URL"}}
  ]
}}

【関連記事ルール】
・relatedは既存記事履歴からURL付き記事がある場合のみ最大3件選ぶ
・存在しないURLや架空URLは作らない
・使える関連記事がなければ related は空配列にする
・関連記事は、今回のテーマ名やジャンル語と近い記事を優先する
・NTR、人妻、寝取らせ、羞恥は近いテーマとして扱う
・個撮、ハメ撮り、ナンパ、カップル、女子大生は近いテーマとして扱う
・童貞、筆下ろし、清楚、OLは近いテーマとして扱う
・関連性が同程度なら5選記事を優先する
・関連記事は必ず3件選ぶ
・記事タイトルに含まれる主要キーワードが一致する記事を優先する

【テーマ】
{safe_theme}

【テーマ名】
{theme_name}

【記事用作品データ】
{json.dumps(prompt_items, ensure_ascii=False, indent=2)}

【既存記事履歴】
{json.dumps(history_items, ensure_ascii=False, indent=2)}
"""


current_theme = load_json("current_theme.json", {})
works = load_json("selected_article_works.json", [])
reviews = load_json("reviews.json", {})
article_history = load_json("article_history.json", [])

internal_works, prompt_items = build_article_works(works, reviews)
history_items = normalize_history_items(article_history)
theme_name = guess_theme_name(current_theme, prompt_items)
works_count = len(internal_works)

if works_count == 0:
    raise Exception("記事用作品データがありません")

prompt = build_prompt(current_theme, prompt_items, history_items, theme_name, works_count)

print("===== PROMPT CHECK =====")
print(prompt[:12000])

article_data = None
last_error = None

for attempt in range(5):

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_NONE"
                    )
                ]
            )
        )

        if response is None:
            raise Exception("Gemini returned None")

        if not getattr(response, "text", None):
            raise Exception(f"Gemini returned no text: {response}")

        article_data = extract_json(response.text)
        validate_json_data(article_data, works_count)

        break

    except Exception as e:

        msg = str(e)

        if "RESOURCE_EXHAUSTED" in msg:
            raise

        if "PROHIBITED_CONTENT" in msg:
            raise

        last_error = e
        article_data = None

        print(
            f"Gemini JSON error attempt {attempt + 1}/5: {e}"
        )

        time.sleep(10 * (attempt + 1))

if article_data is None:
    raise last_error

article = build_article_from_json(article_data, internal_works, theme_name)

output_path = DATA_DIR / "generated_article.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(article)

print("記事生成完了")
print(f"article_path={output_path}")
