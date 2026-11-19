---
name: arxiv-fetch
description: arXiv を検索して候補論文のメタデータ群を取得する手法と、候補メタデータの構造・arXiv 識別子・新着判定・未解説判定の扱いを内包する How スキル。論文収集（paper-fetcher）と論文選定（paper-selector）の両工程から名指しで呼び出される。検索条件の既定値もここに集約する。
---

# arxiv-fetch — arXiv 検索・候補メタデータ取得

arXiv API から候補論文のメタデータを取得し、後続工程が機械的に扱える形式で保存する手法を定義する。論文の収集（検索→保存）と選定（新着・未解説判定）の両方が依拠する共通リファレンス。

## このスキルが規定すること

1. arXiv API の叩き方（`scripts/fetch_arxiv.py`）
2. 検索条件の既定値
3. 候補メタデータの保存フォーマット（後続工程の機械可読インターフェース）
4. arXiv 識別子・新着判定・未解説判定の扱い

## 実行環境

- ランタイム: Python 3.9+
- 実行は `uv run`（プロジェクト共通の実行方法に揃える）。依存ライブラリはなく（標準ライブラリ `urllib` / `xml.etree.ElementTree` のみで arXiv Atom API を扱う）、スクリプト先頭の PEP 723 ブロックで `dependencies = []` を宣言している。メイン環境を汚さない。

## 検索条件の既定値

`/write-article` の引数で検索条件が明示されない場合は以下を既定値とする。

- **対象分野（4 分野）**: ① LNP（脂質ナノ粒子）等のナノ粒子・DDS、② 低分子医薬（CMC 寄り：製剤・原薬・結晶形・製造プロセス・不純物・品質）、③ ワクチン、④ 核酸（mRNA・siRNA・アンチセンス等の核酸医薬）
- 検索式: 「カテゴリのいずれか」AND「キーワードのいずれかをアブストラクトに含む」
  - カテゴリ: `q-bio.BM`, `q-bio.QM`, `q-bio.TO`, `q-bio.MN`, `q-bio.CB`, `q-bio.SC`, `physics.bio-ph`, `physics.chem-ph`, `physics.med-ph`, `cond-mat.soft`, `cond-mat.mtrl-sci`
  - キーワード: lipid nanoparticle / liposome / nanomedicine / drug delivery / small-molecule drug / pharmaceutical / drug formulation / drug product / active pharmaceutical ingredient / vaccine / mRNA / siRNA / oligonucleotide / nucleic acid
- 取得件数: 60 件（arXiv の検索は語形をゆるく拾い分野外も混ざるため多めに取り、選定で絞る）
- 並び順: 投稿日時の新しい順（`submittedDate` 降順）

明示された場合はそれを優先する。カテゴリ・キーワード・件数は `scripts/fetch_arxiv.py` の `--categories` / `--keywords` / `--max-results` で上書きでき、`--query` で arXiv の `search_query` を直接指定することもできる。キーワードを増やしすぎると検索式が長くなり arXiv 側で解釈が崩れる（分野外ばかり返る）ため、目安として 15 語程度までに保つ。

## 候補メタデータの保存フォーマット（機械可読インターフェース）

`scripts/fetch_arxiv.py` は出力先ディレクトリ（`work/<run-id>/papers/`）配下に次を生成する。後続の選定工程はこのフォーマットを唯一の前提として読む。

- `papers/<arxiv_id>.json` — 論文 1 本ごとのメタデータ。フィールド:
  - `arxiv_id`: バージョンを除いた arXiv 識別子（例 `2401.12345`）
  - `version`: 取得時点の最新バージョン（例 `v2`）
  - `title`: タイトル（改行・連続空白は単一スペースに正規化済み）
  - `authors`: 著者名の配列
  - `summary`: アブストラクト
  - `categories`: arXiv カテゴリの配列（先頭が primary）
  - `published`: 初版投稿日時（ISO8601）
  - `updated`: 最終更新日時（ISO8601）
  - `abs_url`: 論文ページ URL（例 `https://arxiv.org/abs/2401.12345`）
  - `pdf_url`: PDF の URL（例 `https://arxiv.org/pdf/2401.12345`）
- `papers/index.json` — 候補一覧。`arxiv_id` / `title` / `published` / `updated` を持つオブジェクトの配列を、`published` 降順で並べたもの。選定工程はまずこれを読んで候補全体を把握する。

## arXiv 識別子・新着判定・未解説判定の扱い

- **識別子の正規化**: arXiv の Atom `id` は `http://arxiv.org/abs/2401.12345v2` 形式で末尾にバージョンが付く。`arxiv_id` はバージョンを除いた `2401.12345` を正準キーとして扱う。同一論文の同定・重複排除はこの `arxiv_id` で行う。
- **新着判定**: 新しさは `published`（初版投稿日時）の降順で評価する。`index.json` は既にこの順で並んでいるため、選定では先頭に近いものほど新しい。
- **未解説判定**: ある `arxiv_id` が既に解説済みかは、`output/` 配下の公開記事に当該 `arxiv_id` が含まれるかで判断する。公開記事は frontmatter に `arxiv_id` を持つ（`japanese-tech-writing` の記事フォーマット規約）。`output/` 内の記事 frontmatter の `arxiv_id` 集合に含まれる候補は「解説済み」とみなして選定対象から除外する。

## 使い方

### 収集（候補メタデータ取得）

出力先ディレクトリを指定して実行する。`<categories>` / `<max-results>` は省略時に上記既定値を用いる。

```bash
uv run .claude/skills/arxiv-fetch/scripts/fetch_arxiv.py \
  --out-dir "work/<run-id>/papers" \
  [--categories q-bio.BM,cond-mat.soft,...] \
  [--keywords "lipid nanoparticle,vaccine,..."] \
  [--max-results 60]
```

実行後、`papers/index.json` と `papers/<arxiv_id>.json` 群が生成される。生成先ディレクトリの絶対パスを収集結果として扱う。

### 選定（新着・未解説の 1 本選び）

選定工程はスクリプトを再実行せず、既に保存された `papers/index.json` と `papers/<arxiv_id>.json` を読み、`output/` の既存記事 frontmatter（`arxiv_id`）と突き合わせて、未解説かつ **対象分野に該当する** もののうち最も新しい 1 本を選ぶ。

- **関連度チェック（必須）**: 候補ごとに `papers/<arxiv_id>.json` の `title` / `summary` を読み、上記「対象分野（4 分野）」のいずれかが論文の **主題** になっているものだけを対象とする。キーワードが付随的に出てくるだけの論文（例: 量子化学の手法論、一般的な材料物性、医薬と無関係な遺伝子発現の理論、疫学の政策モデルなど）は分野外として除外する。創薬一般（標的探索・タンパク質設計など）は 4 分野に直接かからなければ除外し、該当候補が無い場合に限り次点として扱う。
- 選定理由（どの分野に該当するか）を `selected.json` に `selection_reason` フィールドとして追記する。
- 4 分野に該当する未解説候補が 1 本も無い場合は、無理に分野外を選ばず `{"selected": false, "reason": "対象分野の未解説候補なし"}` を書き出す（その日は記事を作らない）。選定結果は `selected.json` として、対象論文の `<arxiv_id>.json` の全フィールドをそのまま写し取って書き出す（後続の解析工程が `pdf_url` / `arxiv_id` / `title` を参照するため）。候補が空・全件解説済みで選定不能な場合は `{"selected": false, "reason": "<理由>"}` を書き出す。
