# fanza-jidou-otonavimatome
全体の流れ
fetch_fanza.py
↓
fetch_reviews.py
↓
fetch_extra.py
↓
filter_works.py
↓
analyze_genres.py
↓
generate_themes.py
↓
score_works.py
↓
select_theme.py
↓
select_works.py
↓
記事生成へ


scripts の役割
1. fetch_fanza.py
何をする？

FANZA APIから作品一覧を取るファイル。

作るデータ
data/works.json
中身
作品ID
タイトル
発売日
URL
画像
ジャンル
レビュー数
評価
rawデータ
今後変更する時

取得件数を増やしたい時はここ。

例：

for offset in [1, 101, 201]:

今は300件取得。
800件にしたいなら、

for offset in [1, 101, 201, 301, 401, 501, 601, 701]:

にする。

2. fetch_reviews.py
何をする？

各作品のレビュー本文をGraphQLから取るファイル。

作るデータ
data/reviews.json
中身
{
  "content_id": [
    {
      "title": "レビュータイトル",
      "rating": 5,
      "comment": "レビュー本文"
    }
  ]
}


今後変更する時

レビュー件数を増やしたい時。

今は1作品あたり最大10件。
増やすならGraphQLの

limit: 10

を変える。

3. fetch_extra.py
何をする？

FANZAから作品説明・お気に入り数・ランキングを取る。

作るデータ
data/extra.json
中身
{
  "content_id": {
    "description": "作品説明",
    "favorite_count": 12345,
    "weekly_rank": 12,
    "monthly_rank": 30
  }
}
今後変更する時

商品説明以外に、追加で欲しい項目がある時。

4. filter_works.py
何をする？

記事に不要な作品を除外する。

入力
data/works.json
出力
data/selected_candidates.json
今除外しているもの
BEST
総集編
VR
長時間作品
福袋
BOX
セット商品
AI生成作品
今後変更する時

「このタイプは記事に入れたくない」と思ったらここを変更。

例：

EXCLUDE_KEYWORDS = [
    "AI生成作品",
    "VR",
    "総集編"
]

ここに追加する。

5. analyze_genres.py
何をする？

集めた作品にどんなジャンルが何件あるか数える。

作るデータ
data/genre_counts.json
中身
[
  {
    "genre": "素人",
    "count": 217
  },
  {
    "genre": "巨乳",
    "count": 98
  }
]
何に使う？

テーマ生成の材料。

6. generate_themes.py
何をする？

ジャンル数を見て、記事テーマを自動生成する。

作るデータ
data/themes.json
例
{
  "name": "素人×巨乳",
  "required": ["素人", "巨乳"],
  "count_hint": 98
}
{
  "name": "素人×中出し×人妻・主婦",
  "required": ["素人", "中出し", "人妻・主婦"],
  "count_hint": 10
}
今後変更する時

テーマ数を増やしたい時はここ。

重要な設定：

MIN_THEME_WORKS = 7

これを上げるとテーマ数は減るが精度は上がる。
下げるとテーマ数は増えるが、10作品集まりにくくなる。

7. score_works.py
何をする？

作品にスコアを付ける。

入力
selected_candidates.json
extra.json
出力
data/scored_works.json
スコア材料
レビュー平均
レビュー数
お気に入り数
週間ランキング
今後変更する時

「お気に入り数をもっと重視したい」
「レビュー数をもっと重視したい」
みたいな時はここを変更。

8. select_theme.py
何をする？

今回の記事テーマを1つ選ぶ。

入力
themes.json
used_themes.json
出力
data/current_theme.json
例
{
  "name": "素人×中出し×人妻・主婦",
  "required": ["素人", "中出し", "人妻・主婦"]
}
今後変更する時

テーマの選び方を変える時。

今はランダム寄り。
将来的には、

候補作品が多いテーマを優先
過去60日使ったテーマを除外
記事化しやすいテーマを優先

にできる。

9. select_works.py
何をする？

現在のテーマに合う作品を10件選ぶ。

入力
current_theme.json
scored_works.json
selected_candidates.json
used_works.json
出力
data/selected_article_works.json
今やっていること
テーマに必要なジャンルを持つ作品だけ選ぶ
同じシリーズを最大2本まで
同じメーカーを最大3本まで
60日以内に使った作品を除外
7件未満ならエラー
今後変更する時

作品選定の精度を上げるならここ。

今問題になっている、

素人×人妻なのに女子大生が混ざる
素人×OLなのに6件しか出ない

もここで調整する。

10. save_history.py
何をする？

記事に使ったテーマ・作品を履歴に保存する。

入力
current_theme.json
selected_article_works.json
出力
used_themes.json
used_works.json
注意

今はまだ本投稿前なので、YAMLから外しておく方が安全。

理由：

記事化していない作品まで使用済みにされる

から。

本当にWordPress投稿まで成功した後に実行するのが正解。

data の役割
works.json

FANZA APIから取った元作品リスト。

reviews.json

レビュー本文DB。

extra.json

作品説明・お気に入り数・ランキングDB。

selected_candidates.json

除外フィルタ後の使える作品リスト。

genre_counts.json

ジャンル別の件数。

themes.json

自動生成された記事テーマ一覧。

current_theme.json

今回の記事テーマ。

scored_works.json

スコア付き作品一覧。

selected_article_works.json

今回の記事に使う作品リスト。

used_themes.json

過去に使ったテーマ履歴。

used_works.json

過去に使った作品履歴。
