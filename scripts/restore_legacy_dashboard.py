"""Restore the stable/legacy Dashboard presentation.

Keep the situational map module, but remove the experimental dashboard-modern
layer and the old satker compatibility bridge from index.html.
"""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "index.html"


def main():
    text = INDEX.read_text(encoding="utf-8")
    original = text

    # Remove the experimental dashboard presentation layer wherever present.
    text = re.sub(r'\s*<link[^>]+dashboard-modern\.css\?v=[^>]+>', '', text, flags=re.I)
    text = re.sub(r'\s*<script[^>]+dashboard-modern\.js\?v=[^>]+></script>', '', text, flags=re.I)

    # Remove deprecated first-class-satker UI wiring. Polda remains a Jatim
    # area handled by the location model instead.
    text = re.sub(r'\s*<script[^>]+satker-ui\.js\?v=[^>]+></script>', '', text, flags=re.I)
    text = re.sub(r'\s*<style[^>]+id=["\']jagat-satker-ui-style["\'][^>]*>.*?</style>', '', text, flags=re.I | re.S)

    INDEX.write_text(text, encoding="utf-8")
    print(f"Legacy dashboard restore: {'CHANGED' if text != original else 'OK'}")


if __name__ == "__main__":
    main()
