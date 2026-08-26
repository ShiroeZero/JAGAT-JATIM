import json
import os
import sys
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from location_engine import detect_location

NEWS_FILE = os.path.join(BASE, "data", "news.json")

def strip_publisher_suffix(title, source):
    title = str(title or "").strip()
    source = str(source or "").strip()
    if not title or not source:
        return title

    # Google News commonly appends the publisher to the title using
    # " - Source", " – Source", " — Source", or " | Source".
    pattern = r"\s+(?:-|–|—|\|)\s*" + re.escape(source) + r"\s*$"
    cleaned = re.sub(pattern, "", title, flags=re.IGNORECASE)
    return cleaned.strip()

def main():
    with open(NEWS_FILE, encoding="utf-8") as f:
        db = json.load(f)

    items = db.get("items", [])
    changed = 0

    for item in items:
        source = item.get("source") or item.get("publisher") or ""
        title_for_location = strip_publisher_suffix(
            item.get("title", ""),
            source,
        )
        result = detect_location(
            title_for_location,
            item.get("description", ""),
        )

        old = (
            item.get("is_jatim"),
            item.get("region"),
            item.get("polres"),
        )

        # Canonicalize Polres from explicit mentions in the title/description.
        # Bare city names are retained as region evidence, not as proof of Polres.
        polres = result.get("polres")

        # A known explicit Polres is a strong Jatim signal.
        is_jatim = True if polres else bool(result.get("is_jatim"))
        region = "Jawa Timur" if is_jatim else "Indonesia"

        item["is_jatim"] = is_jatim
        item["region"] = region
        item["polres"] = polres
        item["location_confidence"] = result.get("confidence", 0)
        item["location_evidence"] = result.get("evidence", [])
        item["location_source"] = result.get("source")

        new = (
            item.get("is_jatim"),
            item.get("region"),
            item.get("polres"),
        )

        if old != new:
            changed += 1

    db["location_engine_version"] = "location-v4"
    db["location_normalized_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    tmp = NEWS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NEWS_FILE)

    print("========================================")
    print("PNM LOCATION NORMALIZATION")
    print("========================================")
    print(f"Records        : {len(items)}")
    print(f"Updated        : {changed}")
    print("Engine         : location-v4")
    print(f"Output         : {NEWS_FILE}")
    print("========================================")

if __name__ == "__main__":
    main()
