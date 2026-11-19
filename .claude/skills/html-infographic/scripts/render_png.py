#!/usr/bin/env python
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""自己完結 HTML を Chromium 系ブラウザ（Edge / Chrome）のヘッドレスモードで PNG 化する。

外部サービス・API キー・追加インストール不要（Windows 標準の Edge で動く）。標準ライブラリのみ。

使い方:
  uv run .claude/skills/html-infographic/scripts/render_png.py --html <cover.html> --out <cover.png> [--width 1920 --height 1080]

終了コード 0 で、出力 PNG の実寸が指定サイズと一致したことを保証する。
"""

import argparse
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import time

CANDIDATES = [
    # Windows（Chrome は同期的に書き出すので優先。Edge はランチャ経由で非同期に書き出すため待機が要る）
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
PATH_NAMES = ["msedge", "google-chrome", "chromium", "chromium-browser", "chrome"]


def find_browser(explicit=None):
    if explicit:
        return explicit
    env = os.environ.get("INFOGRAPHIC_BROWSER")
    if env and os.path.isfile(env):
        return env
    local = os.environ.get("LOCALAPPDATA")
    extra = [os.path.join(local, r"Google\Chrome\Application\chrome.exe")] if local else []
    for c in CANDIDATES + extra:
        if os.path.isfile(c):
            return c
    for n in PATH_NAMES:
        p = shutil.which(n)
        if p:
            return p
    raise SystemExit("Edge / Chrome が見つかりません。--browser でブラウザ実行ファイルを指定してください。")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"PNG ではありません: {path}")
    return struct.unpack(">II", head[16:24])


def main(argv=None):
    ap = argparse.ArgumentParser(description="HTML をヘッドレスブラウザで PNG 化する")
    ap.add_argument("--html", required=True, help="入力 HTML（自己完結。外部リソース不可）")
    ap.add_argument("--out", required=True, help="出力 PNG")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--browser", default=None, help="ブラウザ実行ファイル（省略時は自動検出）")
    ap.add_argument("--wait-ms", type=int, default=3000, help="フォント読込等の待ち時間(ms)")
    args = ap.parse_args(argv)

    html = pathlib.Path(args.html).resolve()
    if not html.is_file():
        raise SystemExit(f"HTML が存在しません: {html}")
    out = pathlib.Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    browser = find_browser(args.browser)
    profile = tempfile.mkdtemp(prefix="infographic-profile-")
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        f"--user-data-dir={profile}",
        "--force-device-scale-factor=1",
        f"--window-size={args.width},{args.height}",
        f"--virtual-time-budget={args.wait_ms}",
        f"--screenshot={out}",
        html.as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    # Edge はランチャが即時終了し、本体が後から PNG を書き出すことがある。安定するまで待つ。
    deadline = time.time() + 30
    last = -1
    while time.time() < deadline:
        if out.is_file():
            size = out.stat().st_size
            if size > 0 and size == last:
                break
            last = size
        time.sleep(1)
    shutil.rmtree(profile, ignore_errors=True)

    if not out.is_file():
        sys.stderr.write(proc.stdout[-2000:] + "\n" + proc.stderr[-2000:] + "\n")
        raise SystemExit(f"PNG が生成されませんでした（browser={browser}, rc={proc.returncode}）")

    w, h = png_size(out)
    if (w, h) != (args.width, args.height):
        raise SystemExit(f"出力サイズ不一致: {w}x{h}（期待 {args.width}x{args.height}）: {out}")

    print(f"rendered {w}x{h} ({out.stat().st_size // 1024} KB) via {os.path.basename(browser)}: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
