"""Idempotently wire the satker UI layer into the existing static frontend."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "index.html"
MARKER = 'satker-ui.js?v=6.6.0'
TAG = f'<script defer src="{MARKER}"></script>'
STYLE = '<style id="jagat-satker-ui-style">.satker-filter-wrap{flex:1;min-width:180px}.satker-filter-wrap select{width:100%}</style>'


def main():
    text = INDEX.read_text(encoding="utf-8")
    changed = False
    if MARKER not in text:
        anchor = "</head>"
        if anchor not in text:
            raise SystemExit("index.html: </head> not found")
        text = text.replace(anchor, f"  {STYLE}\n{TAG}\n{anchor}", 1)
        changed = True
    INDEX.write_text(text, encoding="utf-8")
    print(f"Frontend satker wiring: {'CHANGED' if changed else 'OK'}")


if __name__ == "__main__":
    main()
