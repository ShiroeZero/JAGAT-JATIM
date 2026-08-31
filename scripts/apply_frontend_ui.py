"""Wire the stable frontend layer without the experimental dashboard redesign."""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "index.html"
MAP_SCRIPT_MARKER = 'map-situasional.js?v=6.7.1'
MAP_SCRIPT_TAG = f'<script defer src="{MAP_SCRIPT_MARKER}"></script>'

# The experimental dashboard-modern layer is intentionally disabled.
MODERN_STYLE = re.compile(r'\s*<link[^>]+dashboard-modern\.css\?v=[^>]+>', re.I)
MODERN_SCRIPT = re.compile(r'\s*<script[^>]+dashboard-modern\.js\?v=[^>]+></script>', re.I)
OLD_SCRIPT = re.compile(r'\s*<script[^>]+satker-ui\.js\?v=[^>]+></script>', re.I)
OLD_STYLE = re.compile(r'\s*<style[^>]+id=["\']jagat-satker-ui-style["\'][^>]*>.*?</style>', re.I | re.S)


def main():
    text = INDEX.read_text(encoding="utf-8")
    original = text

    # Return the dashboard to the stable/base presentation.
    text = MODERN_STYLE.sub("", text)
    text = MODERN_SCRIPT.sub("", text)
    text = OLD_SCRIPT.sub("", text)
    text = OLD_STYLE.sub("", text)

    # Keep the stable situational map integration, but never restore the
    # experimental dashboard-modern layer.
    if MAP_SCRIPT_MARKER not in text:
        anchor = "</body>"
        if anchor not in text:
            raise SystemExit("index.html: </body> not found")
        text = text.replace(anchor, f"  {MAP_SCRIPT_TAG}\n{anchor}", 1)

    INDEX.write_text(text, encoding="utf-8")
    print(f"Stable frontend wiring: {'CHANGED' if text != original else 'OK'}")


if __name__ == "__main__":
    main()
