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


def monitoring_dt(item):
    return parse_dt(item.get("collected_at")) or parse_dt(item.get("published_at"))


def is_today(item, date_value):
    dt = monitoring_dt(item)
    return bool(dt and dt.date() == date_value)


def priority_value(value):
    return str(value or "").strip().lower()


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

    date_value = today_db.get("date")
    if not date_value:
        fail("today.json missing date")
    try:
        today = datetime.strptime(str(date_value), "%Y-%m-%d").date()
    except ValueError:
        fail(f"Invalid today date: {date_value}")

    # --------------------------------------------------------
    # ID integrity
    # --------------------------------------------------------
    news_ids = [x.get("id") for x in news if x.get("id")]
    case_ids = [x.get("case_id") for x in cases if x.get("case_id")]
    if len(news_ids) != len(set(news_ids)):
        errors.append("Duplicate news IDs detected")
    if len(case_ids) != len(set(case_ids)):
        errors.append("Duplicate case IDs detected")

    news_map = {x["id"]: x for x in news if x.get("id")}
    case_map = {x["case_id"]: x for x in cases if x.get("case_id")}

    # --------------------------------------------------------
    # News -> Case and Case -> News integrity
    # --------------------------------------------------------
    for item in news:
        cid = item.get("case_id")
        if cid and cid not in case_map:
            errors.append(f"news {item.get('id')} points to missing {cid}")

    seen_case_articles = {}
    for case in cases:
        cid = case.get("case_id")
        article_ids = list(case.get("article_ids", []))
        article_objects = list(case.get("articles", []))

        if len(article_ids) != len(set(article_ids)):
            errors.append(f"{cid} has duplicate article_ids")

        object_ids = [a.get("id") for a in article_objects if a.get("id")]
        if set(object_ids) != set(article_ids):
            errors.append(f"{cid} article_ids/articles mismatch")

        for aid in article_ids:
            if aid not in news_map:
                errors.append(f"{cid} points to missing article {aid}")
                continue
            if news_map[aid].get("case_id") != cid:
                errors.append(
                    f"{cid}/{aid} reverse link mismatch: "
                    f"news.case_id={news_map[aid].get('case_id')}"
                )
            previous = seen_case_articles.get(aid)
            if previous and previous != cid:
                errors.append(
                    f"article {aid} appears in multiple cases: {previous}, {cid}"
                )
            seen_case_articles[aid] = cid

    # --------------------------------------------------------
    # Canonical Case score validation
    # Same active_today definition as process_cases.compute_case_priority.
    # --------------------------------------------------------
    for case in cases:
        cid = case.get("case_id")
        stored_score = case.get("attention_score", case.get("priority_score"))
        if stored_score is None:
            errors.append(f"{cid} missing attention_score")
            continue

        active_today = sum(
            1
            for article in case.get("articles", [])
            if is_today(article, today)
        )

        recalculated = case_attention(
            case.get("articles", []),
            case=case,
            active_today=active_today,
        )
        expected_score = int(recalculated.get("score", 0))
        if int(stored_score) != expected_score:
            errors.append(
                f"{cid} attention_score mismatch: stored={stored_score}, "
                f"expected={expected_score}, active_today={active_today}"
            )

        expected_priority = priority_value(recalculated.get("priority"))
        actual_priority = priority_value(case.get("priority"))
        if actual_priority != expected_priority:
            errors.append(
                f"{cid} legacy priority mismatch: stored={actual_priority}, "
                f"expected={expected_priority}"
            )

    # --------------------------------------------------------
    # Today counts — monitoring date = collected_at, published_at fallback.
    # --------------------------------------------------------
    actual_today = [x for x in news if is_today(x, today)]
    actual_news_count = len(actual_today)
    actual_negative = sum(1 for x in actual_today if priority_value(x.get("scope")) == "negative")
    actual_positive = sum(1 for x in actual_today if priority_value(x.get("scope")) == "positive")
    actual_case_scope = sum(1 for x in actual_today if priority_value(x.get("scope")) == "case")
    actual_neutral = sum(1 for x in actual_today if priority_value(x.get("scope")) == "neutral")
    actual_jatim_items = [x for x in actual_today if x.get("is_jatim") is True]
    actual_jatim = len(actual_jatim_items)
    actual_article_high = sum(1 for x in actual_today if priority_value(x.get("priority")) == "high")

    # Active cases today use article activity today, not Case persistence.
    active_today_cases = [
        c
        for c in cases
        if any(is_today(a, today) for a in c.get("articles", []))
    ]
    actual_case_high_global = sum(
        1 for c in active_today_cases if priority_value(c.get("priority")) == "high"
    )
    actual_case_high_jatim = sum(
        1 for c in active_today_cases
        if c.get("is_jatim") is True and priority_value(c.get("priority")) == "high"
    )

    summary = today_db.get("summary", {})
    checks = [
        (int(summary.get("news_today", 0) or 0), actual_news_count, "today.json news count"),
        (int(summary.get("negative_today", 0) or 0), actual_negative, "today.json negative count"),
        (int(summary.get("jatim_news", 0) or 0), actual_jatim, "today.json Jatim count"),
        (int(summary.get("priority_high", 0) or 0), actual_case_high_global, "today.json global case-high count"),
        (int(summary.get("article_priority_high", 0) or 0), actual_article_high, "today.json article-high count"),
    ]

    jatim_db = today_db.get("jatim", {})
    checks.extend([
        (
            int(jatim_db.get("news_today", 0) or 0),
            actual_jatim,
            "today.json Jatim dashboard news count",
        ),
        (
            int(jatim_db.get("negative_today", 0) or 0),
            sum(1 for x in actual_jatim_items if priority_value(x.get("scope")) == "negative"),
            "today.json Jatim negative count",
        ),
        (
            int(jatim_db.get("case_high_active", 0) or 0),
            actual_case_high_jatim,
            "today.json Jatim case-high count",
        ),
    ])

    for stored, actual, label in checks:
        if stored != actual:
            errors.append(f"{label} mismatch: stored={stored}, actual={actual}")

    # --------------------------------------------------------
    # Snapshot article IDs
    # --------------------------------------------------------
    stored_article_ids = set(today_db.get("news", {}).get("article_ids", []))
    actual_article_ids = {x.get("id") for x in actual_today if x.get("id")}
    if stored_article_ids != actual_article_ids:
        errors.append(
            "today.json article_ids do not match raw news.json "
            "using monitoring date"
        )

    # --------------------------------------------------------
    # Semantic location validation
    # --------------------------------------------------------
    scripts_dir = os.path.join(BASE, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from location_engine import detect_location, POLRES_MAP
        if len(POLRES_MAP) != 39:
            errors.append(
                f"location master expected 39 Polres, found={len(POLRES_MAP)}"
            )
        for item in news:
            expected = detect_location(
                item.get("title", ""),
                source=item.get("source") or item.get("publisher") or "",
            )
            actual = (
                item.get("is_jatim"),
                item.get("region"),
                item.get("locality") or "",
                item.get("polres"),
            )
            expected_tuple = (
                expected["is_jatim"],
                expected["region"],
                expected["locality"],
                expected["polres"],
            )
            if actual != expected_tuple:
                errors.append(
                    f"location mismatch {item.get('id')}: "
                    f"stored={actual}, expected={expected_tuple}"
                )
    except Exception as exc:
        errors.append(f"location semantic validation unavailable: {exc}")

    if errors:
        for error in errors[:50]:
            print("ERROR:", error)
        fail(f"validation failed with {len(errors)} issue(s)")

    print("========================================")
    print("JAGAT SYSTEM DATA VALIDATION V6.5.2")
    print("========================================")
    print(f"News records          : {len(news)}")
    print(f"Case records          : {len(cases)}")
    print(f"Case links            : {len(seen_case_articles)}")
    print(f"Today date            : {today}")
    print(f"News today            : {actual_news_count}")
    print(f"Jatim today           : {actual_jatim}")
    print(f"Negative today        : {actual_negative}")
    print(f"Global case-high      : {actual_case_high_global}")
    print(f"Jatim case-high       : {actual_case_high_jatim}")
    print(f"Article high today    : {actual_article_high}")
    print("----------------------------------------")
    print("Consistency            : OK")
    print("Today snapshot         : OK")
    print("Global/Jatim scope     : OK")
    print("Case score validation  : OK")
    print("Case relationships     : OK")
    print("========================================")


if __name__ == "__main__":
    main()
