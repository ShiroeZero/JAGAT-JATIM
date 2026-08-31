"""Assign first-class organisational unit (satker) metadata.

JAGAT keeps Polres/Polsek as geographic enforcement entities. Polda Jatim is
represented separately as an organisational satker and must never be treated
as a 40th Polres or a locality.
"""
import json
import os
import re
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_FILE = os.path.join(BASE, "data", "news.json")
CASE_FILE = os.path.join(BASE, "data", "case_clusters.json")

SATKER_POLDA_JATIM = "POLDA JAWA TIMUR"
POLDA_PATTERNS = [
    r"\bpolda\s+(?:jawa\s+timur|jatim)\b",
    r"\bkapolda\s+(?:jawa\s+timur|jatim)\b",
]


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_satker(item):
    title = normalize(item.get("title", ""))
    if any(re.search(pattern, title) for pattern in POLDA_PATTERNS):
        return SATKER_POLDA_JATIM
    return None


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def main():
    with open(NEWS_FILE, encoding="utf-8") as f:
        news_db = json.load(f)
    with open(CASE_FILE, encoding="utf-8") as f:
        case_db = json.load(f)

    news = news_db.get("items", [])
    cases = case_db.get("cases", [])

    by_id = {}
    polda_news = 0
    for item in news:
        satker = detect_satker(item)
        if satker:
            item["satker"] = satker
            polda_news += 1
        else:
            item.pop("satker", None)
        if item.get("id"):
            by_id[item["id"]] = item

    polda_cases = 0
    for case in cases:
        linked = [by_id.get(aid) for aid in case.get("article_ids", [])]
        linked = [x for x in linked if x]
        # Satker attribution is orthogonal to geographic Polres attribution.
        # One explicit Polda Jatim-linked article is enough to expose the case
        # under the Polda satker filter; this does not change its Polres/locality.
        if any(x.get("satker") == SATKER_POLDA_JATIM for x in linked):
            case["satker"] = SATKER_POLDA_JATIM
            polda_cases += 1
        else:
            case.pop("satker", None)

        for article in case.get("articles", []):
            source = by_id.get(article.get("id"))
            if source and source.get("satker"):
                article["satker"] = source["satker"]
            else:
                article.pop("satker", None)

    now = datetime.now(timezone.utc).isoformat()
    news_db["satker_engine_version"] = "satker-v1.0.0"
    news_db["satker_normalized_at"] = now
    case_db["satker_engine_version"] = "satker-v1.0.0"
    case_db["satker_normalized_at"] = now

    save(NEWS_FILE, news_db)
    save(CASE_FILE, case_db)

    print("========================================")
    print("JAGAT SATKER NORMALIZATION V1.0.0")
    print("========================================")
    print(f"News records : {len(news)}")
    print(f"Polda news   : {polda_news}")
    print(f"Polda cases  : {polda_cases}")
    print(f"Satker       : {SATKER_POLDA_JATIM}")
    print("========================================")


if __name__ == "__main__":
    main()
