import json
import os
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from location_engine import detect_location

NEWS_FILE = os.path.join(BASE, "data", "news.json")
ENGINE_VERSION = "location-v6.4-title-only"


def normalize_news_record(item):
    result = detect_location(
        item.get("title", ""),
        source=item.get("source") or item.get("publisher") or "",
    )
    item["is_jatim"] = bool(result["is_jatim"])
    item["region"] = result["region"]
    item["locality"] = result["locality"]
    item["area_label"] = result["area_label"]
    item["polres"] = result["polres"]
    item["location_confidence"] = result["confidence"]
    item["location_evidence"] = result["evidence"]
    item["location_source"] = "title"
    return item


def main():
    with open(NEWS_FILE, encoding="utf-8") as f:
        db = json.load(f)

    items = db.get("items", [])
    changed = 0
    jatim = 0
    outside = 0

    for item in items:
        before = {
            k: item.get(k)
            for k in ("is_jatim", "region", "locality", "area_label", "polres", "location_confidence", "location_evidence")
        }
        normalize_news_record(item)
        after = {
            k: item.get(k)
            for k in before
        }
        if before != after:
            changed += 1
        if item.get("is_jatim"):
            jatim += 1
        else:
            outside += 1

    db["location_engine_version"] = ENGINE_VERSION
    db["location_normalized_at"] = datetime.now(timezone.utc).isoformat()

    tmp = NEWS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NEWS_FILE)

    print("========================================")
    print("JAGAT LOCATION NORMALIZATION V6.4")
    print("TITLE ONLY")
    print("========================================")
    print(f"News records : {len(items)}")
    print(f"Jawa Timur   : {jatim}")
    print(f"LUAR JATIM   : {outside}")
    print(f"Changed      : {changed}")
    print(f"Engine       : {ENGINE_VERSION}")
    print("========================================")


if __name__ == "__main__":
    main()
