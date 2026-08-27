import json
import os
import sys
from datetime import datetime, timezone

from zoneinfo import ZoneInfo
from analysis_engine import case_attention

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {
    "news": os.path.join(BASE, "data", "news.json"),
    "cases": os.path.join(BASE, "data", "case_clusters.json"),
    "today": os.path.join(BASE, "data", "today.json"),
}

TZ = ZoneInfo("Asia/Jakarta")
RANK = {"low": 1, "medium": 2, "high": 3}

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def fail(message):
    print("ERROR:", message)
    raise SystemExit(1)

def parse_dt(value):
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ)
    except Exception:
        return None

def is_today(item, date_value):
    dt = parse_dt(item.get("collected_at") or item.get("published_at"))
    return bool(dt and dt.date() == date_value)

def priority_for_score(score, severity=0):
    score = int(score or 0)
    severity = int(severity or 0)
    if severity >= 40 or (score >= 65 and severity >= 25):
        return "high"
    if score >= 40:
        return "medium"
    return "low"

def main():
    for name, path in FILES.items():
        if not os.path.exists(path):
            fail(f"{name} file missing: {path}")

    news_db = load(FILES["news"])
    case_db = load(FILES["cases"])
    today_db = load(FILES["today"])

    news = news_db.get("items", [])
    cases = case_db.get("cases", [])

    errors = []
    news_ids = [x.get("id") for x in news if x.get("id")]
    case_ids = [x.get("case_id") for x in cases if x.get("case_id")]

    if len(news_ids) != len(set(news_ids)):
        errors.append("Duplicate news IDs detected")
    if len(case_ids) != len(set(case_ids)):
        errors.append("Duplicate case IDs detected")

    news_map = {x["id"]: x for x in news if x.get("id")}
    case_map = {x["case_id"]: x for x in cases if x.get("case_id")}
    seen_case_articles = set()

    for item in news:
        cid = item.get("case_id")
        if cid and cid not in case_map:
            errors.append(f"news {item.get('id')} points to missing {cid}")

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
            elif news_map[aid].get("case_id") != cid:
                errors.append(f"{cid}/{aid} reverse link mismatch: news.case_id={news_map[aid].get('case_id')}")
            if aid in seen_case_articles:
                errors.append(f"article {aid} appears in multiple cases")
            seen_case_articles.add(aid)

        score = case.get("attention_score", case.get("priority_score"))
        if score is None:
            errors.append(f"{cid} missing attention_score")
        else:
            recalculated = case_attention(case.get("articles", []), case=case, active_today=0)
            expected_score = int(recalculated.get("score", 0))
            if int(score) != expected_score:
                errors.append(f"{cid} attention_score mismatch: stored={score}, expected={expected_score}")
            expected_priority = str(recalculated.get("priority") or "low").lower()
            actual_priority = str(case.get("priority") or "low").lower()
            if actual_priority != expected_priority:
                errors.append(f"{cid} legacy priority mismatch: stored={actual_priority}, expected={expected_priority}")

    date_value = today_db.get("date")
    if not date_value:
        fail("today.json missing date")
    try:
        today = datetime.strptime(str(date_value), "%Y-%m-%d").date()
    except ValueError:
        fail(f"Invalid today date: {date_value}")

    actual_today = [x for x in news if is_today(x, today)]
    actual_news_count = len(actual_today)
    actual_negative = sum(1 for x in actual_today if str(x.get("scope") or "").lower() == "negative")
    actual_positive = sum(1 for x in actual_today if str(x.get("scope") or "").lower() == "positive")
    actual_case_scope = sum(1 for x in actual_today if str(x.get("scope") or "").lower() == "case")
    actual_neutral = sum(1 for x in actual_today if str(x.get("scope") or "").lower() == "neutral")
    actual_jatim = sum(1 for x in actual_today if x.get("is_jatim") is True)
    actual_article_high = sum(1 for x in actual_today if str(x.get("priority") or "").lower() == "high")

    today_summary = today_db.get("summary", {})
    stored_news = int(today_summary.get("news_today", 0) or 0)
    stored_negative = int(today_summary.get("negative_today", 0) or 0)
    stored_jatim = int(today_summary.get("jatim_news", 0) or 0)
    stored_case_high = int(today_summary.get("priority_high", 0) or 0)
    stored_article_high = int(today_summary.get("article_priority_high", today_db.get("news", {}).get("priority_high", 0)) or 0)

    active_today_cases = [
        c for c in cases
        if any(is_today(a, today) for a in c.get("articles", []))
    ]
    actual_case_high = sum(1 for c in active_today_cases if str(c.get("priority") or "").lower() == "high")

    checks = [
        (stored_news, actual_news_count, "today.json news count"),
        (stored_negative, actual_negative, "today.json negative count"),
        (stored_jatim, actual_jatim, "today.json Jatim count"),
        (stored_case_high, actual_case_high, "today.json case-high count"),
        (stored_article_high, actual_article_high, "today.json article-high count"),
    ]

    jatim_db = today_db.get("jatim", {})
    checks.extend([
        (int(jatim_db.get("news_today", 0) or 0), actual_jatim, "today.json Jatim dashboard news count"),
        (
            int(jatim_db.get("negative_today", 0) or 0),
            sum(1 for x in actual_today if x.get("is_jatim") is True and str(x.get("scope") or "").lower() == "negative"),
            "today.json Jatim negative count",
        ),
        (
            int(jatim_db.get("case_high_active", 0) or 0),
            actual_case_high,
            "today.json Jatim case-high count",
        ),
    ])
    for stored, actual, label in checks:
        if stored != actual:
            errors.append(f"{label} mismatch: stored={stored}, actual={actual}")

    stored_article_ids = set(today_db.get("news", {}).get("article_ids", []))
    actual_article_ids = {x.get("id") for x in actual_today if x.get("id")}
    if stored_article_ids != actual_article_ids:
        errors.append("today.json article_ids do not match raw news.json")

    # Semantic location validation: stored location must be reproducible from title only.
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from location_engine import detect_location, POLRES_MAP
        if len(POLRES_MAP) != 39:
            errors.append(f"location master expected 39 Polres, found={len(POLRES_MAP)}")
        for item in news:
            expected = detect_location(item.get("title", ""), source=item.get("source") or item.get("publisher") or "")
            fields = (item.get("is_jatim"), item.get("region"), item.get("locality") or "", item.get("polres"))
            actual = (expected["is_jatim"], expected["region"], expected["locality"], expected["polres"])
            if fields != actual:
                errors.append(
                    f"location mismatch {item.get('id')}: stored={fields}, expected={actual}"
                )
    except Exception as exc:
        errors.append(f"location semantic validation unavailable: {exc}")

    if errors:
        for error in errors[:50]:
            print("ERROR:", error)
        fail(f"validation failed with {len(errors)} issue(s)")

    print("========================================")
    print("JAGAT SYSTEM DATA VALIDATION V6.5")
    print("========================================")
    print(f"News records        : {len(news)}")
    print(f"Case records        : {len(cases)}")
    print(f"Case links          : {len(seen_case_articles)}")
    print(f"Today date          : {today}")
    print(f"Actual news today   : {actual_news_count}")
    print(f"Stored news today   : {stored_news}")
    print(f"Negative today      : {actual_negative}")
    print(f"Positive today      : {actual_positive}")
    print(f"Case scope today    : {actual_case_scope}")
    print(f"Neutral today       : {actual_neutral}")
    print(f"Jatim today         : {actual_jatim}")
    print(f"Case high today     : {actual_case_high}")
    print(f"Article high today  : {actual_article_high}")
    print("========================================")
    print("Consistency         : OK")
    print("Today snapshot      : OK")
    print("Case relationships  : OK")
    print("========================================")

if __name__ == "__main__":
    main()
