#!/usr/bin/env python
# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow"]
# ///
"""gpt-image が出力した PNG を指定解像度へリサイズする（macOS の sips の代替。Windows / macOS / Linux 共通）。

描画は一切行わない。既存 PNG の拡大縮小（LANCZOS）のみを行う後処理専用スクリプト。
codex-imagegen の「戻り値の確認」から `uv run` で呼び出す。

使い方:
  uv run .claude/skills/codex-imagegen/scripts/resize_png.py --in <png> --width 1920 --height 1080 [--out <png>]
"""

import argparse
import os
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="PNG を指定解像度へリサイズする（sips 代替）")
    parser.add_argument("--in", dest="src", required=True, help="入力 PNG のパス")
    parser.add_argument("--width", type=int, required=True, help="出力幅(px)")
    parser.add_argument("--height", type=int, required=True, help="出力高さ(px)")
    parser.add_argument("--out", default=None, help="出力先（省略時は入力を上書き）")
    args = parser.parse_args(argv)

    from PIL import Image

    if not os.path.isfile(args.src):
        raise SystemExit(f"入力 PNG が存在しません: {args.src}")

    out = args.out or args.src
    with Image.open(args.src) as im:
        before = im.size
        if before == (args.width, args.height):
            resized = im.copy()
        else:
            resized = im.resize((args.width, args.height), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    resized.save(out, format="PNG")

    print(f"resize {before[0]}x{before[1]} -> {args.width}x{args.height}: {os.path.abspath(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
