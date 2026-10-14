"""Non-destructive canonical URL duplicate annotation for data/news.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))
from article_identity import annotate_duplicate_articles

NEWS_FILE = BASE / "data" / "news.json"


def main() -> None:
    if not NEWS_FILE.exists():
        raise SystemExit(f"Required dataset missing: {NEWS_FILE}")
    db = json.loads(NEWS_FILE.read_text(encoding="utf-8-sig"))
    if not isinstance(db, dict) or not isinstance(db.get("items"), list):
        raise SystemExit("Unexpected data/news.json schema; expected object with items[]")
    items = db["items"]
    before_count = len(items)
    stats = annotate_duplicate_articles(items)
    if len(items) != before_count:
        raise SystemExit("Safety check failed: article record count changed")
    db["article_identity_version"] = "canonical-url-v1"
    db["article_identity_audit"] = {
        **stats,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "non-destructive; source records and raw URLs preserved",
    }
    tmp = NEWS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(NEWS_FILE)
    print("JAGAT CANONICAL ARTICLE IDENTITY")
    for key, value in stats.items():
        print(f"{key}: {value}")
    print(f"records_preserved: {len(items)}")


if __name__ == "__main__":
    main()
