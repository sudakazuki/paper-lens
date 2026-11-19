---
name: html-infographic
description: 記事冒頭インフォグラフィック（cover.png）を、自己完結 HTML（インライン CSS＋インライン SVG）で組み立て、Edge / Chrome のヘッドレスモードで 1920x1080 の PNG に変換する画像生成手段。API キー・有料プラン不要で日本語文字を正確に出せる。write-article の article-image-generator が使用する（Codex 画像生成が使えない環境向けの既定手段）。
---

# html-infographic — HTML/SVG で描いて PNG 化する画像生成手段

## 目的

`cover.png` を、生成 AI ではなく **決定論的な HTML/CSS/SVG** で描き、ヘッドレスブラウザで PNG 化する。外部サービス・API キー・有料プランが不要で、日本語テキストを一字一句正確に描画できる。デザインの中身（何を描くか・品質基準・スタイル）は `infographic-design` が単一真実源であり、本スキルは「どう描いて PNG にするか」だけを定める。

## 前提条件

- Chrome または Microsoft Edge がインストールされていること（Windows は Edge が標準搭載）。自動検出できない場合は `--browser` か環境変数 `INFOGRAPHIC_BROWSER` で実行ファイルを指定する。
- `uv` が PATH に通っていること。

## 手順

1. **HTML を書く** — `cover.png` と同じディレクトリに `cover.html` を Write する（例: `work/<run-id>/images/cover.html`）。下記「HTML 規約」に従う。
2. **PNG 化する** — リポジトリ直下で実行する（`Bash` ツール。タイムアウトは 180000 ms 程度）:
   ```bash
   uv run .claude/skills/html-infographic/scripts/render_png.py --html <cover.html の絶対パス> --out <cover.png の絶対パス>
   ```
   終了コード 0 で `rendered 1920x1080 ...` が出れば成功（実寸が 1920x1080 であることをスクリプトが検証済み）。非ゼロなら失敗。
3. **目視確認する** — 生成した PNG を `Read` ツールで開き、文字の見切れ・重なり・はみ出し・空白の偏りがないかを確認する。問題があれば `cover.html` を直して 2 からやり直す（最大 3 回）。
4. **再生成モード** — レビュー指摘を受けたときは既存の `cover.html` を Read して指摘箇所だけを編集し、2〜3 を行う（作り直さず差分修正。良い部分は壊さない）。`cover.html` が無い場合は新規に書く。

## HTML 規約

- **自己完結**: 1 ファイルに完結させる。外部 CSS・Web フォント・画像・スクリプトを読み込まない（オフラインで同じ結果になるように）。JavaScript は使わない。
- **キャンバス固定**: `html, body { margin:0; width:1920px; height:1080px; overflow:hidden; }`。すべての要素をこの中に収める（はみ出しはそのまま見切れになる）。
- **フォント**: `font-family: "Yu Gothic UI", "Yu Gothic", "Meiryo", "Hiragino Sans", "Noto Sans JP", sans-serif;`（Windows / macOS どちらでも日本語が出る並び）。数字を強調する場合も同じファミリーで太字・大きめにする。
- **文字サイズの下限**: 本文・ラベルは 28px 以上、見出しは 44px 以上、主題タイトルは 72px 以上、強調数値は 80px 以上を目安にする（縮小表示でも判読できるように）。
- **図的要素はインライン SVG または CSS 図形で描く**: 矢印・アイコン・棒グラフ・分布の形・温度計などは `<svg>` の `rect / circle / path / line / polygon / text` で描く。グラフの棒の長さなど数値に対応する図は、`article.md` の数値に比例させる（見た目で誇張しない）。
- **レイアウト**: CSS Grid / Flexbox で 3〜5 個の情報ブロックを、主題 → 課題 → 手法 → 結果の順に視線が流れるよう配置する。ブロックには番号やラベルを付ける。
- **配色**: `infographic-design` のスタイル統一仕様（パステル基調・アクセント 1〜2 色・十分なコントラスト）に従い、色は CSS 変数（`:root { --bg: ...; }`）にまとめる。
- **テキストの根拠**: 画像内の文言・数値は `infographic-design` の「画像内テキストの根拠規約」に従い、`article.md` から取る。

## 戻り値の確認

1. `render_png.py` の終了コードが 0 であること。
2. 期待パスに PNG が実在し、1920x1080 であること（スクリプトが検証）。
3. `Read` による目視で、見切れ・重なり・判読不能な文字がないこと。

いずれかを満たせない場合は失敗扱いとし、呼び出し側の中断ポリシーに従う。

## 参考: Codex 画像生成へ戻す場合

ChatGPT Plus 以上のプランで Codex の組み込み画像生成が使える環境では、`codex-imagegen` スキルを使う方式に戻せる（`article-image-generator` の「使用するスキル」を差し替える）。Free プランの Codex では画像生成ツールが提供されないため、本スキルを既定とする。
