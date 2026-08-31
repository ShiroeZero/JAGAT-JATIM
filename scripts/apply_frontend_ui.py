"""Idempotently wire the focused JAGAT dashboard presentation layer."""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "index.html"
STYLE_MARKER = 'dashboard-modern.css?v=6.7.0'
SCRIPT_MARKER = 'dashboard-modern.js?v=6.7.0'
STYLE_TAG = f'<link rel="stylesheet" href="{STYLE_MARKER}">'
SCRIPT_TAG = f'<script defer src="{SCRIPT_MARKER}"></script>'

OLD_SCRIPT = re.compile(r'\s*<script[^>]+satker-ui\.js\?v=[^>]+></script>', re.I)
OLD_STYLE = re.compile(r'\s*<style[^>]+id=["\']jagat-satker-ui-style["\'][^>]*>.*?</style>', re.I | re.S)


def main():
    text = INDEX.read_text(encoding="utf-8")
    original = text

    # The dashboard no longer exposes a separate "Satker" filter.
    text = OLD_SCRIPT.sub("", text)
    text = OLD_STYLE.sub("", text)

    if STYLE_MARKER not in text:
        anchor = "</head>"
        if anchor not in text:
            raise SystemExit("index.html: </head> not found")
        text = text.replace(anchor, f"  {STYLE_TAG}\n{anchor}", 1)

    if SCRIPT_MARKER not in text:
        anchor = "</body>"
        if anchor not in text:
            raise SystemExit("index.html: </body> not found")
        text = text.replace(anchor, f"  {SCRIPT_TAG}\n{anchor}", 1)

    INDEX.write_text(text, encoding="utf-8")
    print(f"Frontend UI wiring: {'CHANGED' if text != original else 'OK'}")


if __name__ == "__main__":
    main()
