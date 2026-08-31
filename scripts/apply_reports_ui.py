"""Idempotently wire the JAGAT report module into the static frontend."""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "index.html"
STYLE_MARKER = 'laporan.css?v=7.0.0'
SCRIPT_MARKER = 'laporan.js?v=7.0.0'
STYLE_TAG = f'<link rel="stylesheet" href="{STYLE_MARKER}">'
SCRIPT_TAG = f'<script defer src="{SCRIPT_MARKER}"></script>'


def main():
    text = INDEX.read_text(encoding="utf-8")
    original = text

    # Keep the report view as a lightweight hook. laporan.js replaces its
    # placeholder with the real generator when the menu is opened.
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

    # Normalize duplicate copies from prior runs.
    text = re.sub(r'(\s*<link rel="stylesheet" href="laporan\.css\?v=7\.0\.0">){2,}', r'\1', text)
    text = re.sub(r'(\s*<script defer src="laporan\.js\?v=7\.0\.0"></script>){2,}', r'\1', text)

    INDEX.write_text(text, encoding="utf-8")
    print(f"Report UI wiring: {'CHANGED' if text != original else 'OK'}")


if __name__ == "__main__":
    main()
