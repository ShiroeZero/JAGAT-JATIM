import json
import os
import sys
from collections import Counter
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

FILES = {
    "news": os.path.join(BASE, "data", "news.json"),
    "cases": os.path.join(BASE, "data", "case_clusters.json"),
    "today": os.path.join(BASE, "data", "today.json"),
}

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def fail(message):
    print("ERROR:", message)
    raise SystemExit(1)

def main():
    for name, path in FILES.items():
        if not os.path.exists(path):
            fail(f"{name} file missing: {path}")

    news_db = load(FILES["news"])
    case_db = load(FILES["cases"])
    today = load(FILES["today"])

    news = news_db.get("items", [])
    cases = case_db.get("cases", [])

    news_ids = [x.get("id") for x in news if x.get("id")]
    if len(news_ids) != len(set(news_ids)):
        fail("Duplicate news IDs detected")

    case_ids = [x.get("case_id") for x in cases if x.get("case_id")]
    if len(case_ids) != len(set(case_ids)):
        fail("Duplicate case IDs detected")

    case_map = {x["case_id"]: x for x in cases}
    news_map = {x["id"]: x for x in news if x.get("id")}

    errors = []

    for item in news:
        case_id = item.get("case_id")
        if case_id and case_id not in case_map:
            errors.append(f"news {item.get('id')} points to missing {case_id}")

    seen_case_articles = set()

    for case in cases:
        cid = case.get("case_id")
        article_ids = case.get("article_ids", [])
        article_objects = case.get("articles", [])

        if len(article_ids) != len(set(article_ids)):
            errors.append(f"{cid} has duplicate article_ids")

        object_ids = [a.get("id") for a in article_objects if a.get("id")]
        if set(object_ids) != set(article_ids):
            errors.append(f"{cid} article_ids/articles mismatch")

        for aid in article_ids:
            if aid not in news_map:
                errors.append(f"{cid} points to missing article {aid}")
            else:
                if news_map[aid].get("case_id") != cid:
                    errors.append(
                        f"{cid}/{aid} reverse link mismatch: "
                        f"news.case_id={news_map[aid].get('case_id')}"
                    )
            if aid in seen_case_articles:
                errors.append(f"article {aid} appears in multiple cases")
            seen_case_articles.add(aid)

        priorities = [
            {"low": 1, "medium": 2, "high": 3}.get(
                str(a.get("priority") or "low").lower(), 1
            )
            for a in article_objects
        ]
        if priorities:
            expected = max(priorities)
            actual = {"low": 1, "medium": 2, "high": 3}.get(
                str(case.get("priority") or "low").lower(), 1
            )
            if actual != expected:
                errors.append(f"{cid} priority is not canonical from articles")

    if errors:
        for error in errors[:50]:
            print("ERROR:", error)
        fail(f"validation failed with {len(errors)} issue(s)")

    print("========================================")
    print("PNM SYSTEM DATA VALIDATION")
    print("========================================")
    print(f"News records : {len(news)}")
    print(f"Case records : {len(cases)}")
    print(f"Case links   : {len(seen_case_articles)}")
    print(f"Today date   : {today.get('date')}")
    print(f"News today   : {today.get('summary',{}).get('news_today',0)}")
    print(f"Cases today  : {today.get('summary',{}).get('cases_today',0)}")
    print("Consistency  : OK")
    print("========================================")

if __name__ == "__main__":
    main()
