import json
import os
from collections import Counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_FILE = os.path.join(BASE, "data", "news.json")
CASE_FILE = os.path.join(BASE, "data", "case_clusters.json")
SOCIAL_FILE = os.path.join(BASE, "data", "social.json")
TODAY_FILE = os.path.join(BASE, "data", "today.json")
ARCHIVE_DIR = os.path.join(BASE, "data", "archive")

TZ = ZoneInfo("Asia/Jakarta")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

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

def is_today(item, today):
    reference = (
        parse_dt(item.get("collected_at"))
        or parse_dt(item.get("published_at"))
    )
    return bool(reference and reference.date() == today)

def article_is_negative(item):
    scope = str(item.get("scope") or "").lower()
    return scope == "negative"

def active_case_today(case, today):
    for article in case.get("articles", []):
        if is_today(article, today):
            return True
    return False

def priority_rank(value):
    return {"low": 1, "medium": 2, "high": 3}.get(
        str(value or "low").lower(), 1
    )

def build_region_stats(items):
    # Province is the parent; concrete locality is the child. We never
    # expose "Jawa Timur" as a peer category beside Madiun/Batu/etc.
    counter = Counter()
    for item in items:
        if item.get("is_jatim") is not True:
            continue
        locality = str(item.get("locality") or "").strip()
        if locality:
            counter[locality] += 1
    return [{"name": name, "count": count} for name, count in counter.most_common()]

def build_polres_stats(items):
    counter = Counter(
        item.get("polres")
        for item in items
        if item.get("polres")
    )
    return [
        {"name": name, "count": count}
        for name, count in counter.most_common()
    ]

def build_category_stats(items):
    counter = Counter(
        str(item.get("category") or "NETRAL / LAINNYA")
        for item in items
    )
    return [
        {"name": name, "count": count}
        for name, count in counter.most_common()
    ]

def build_snapshot():
    now = datetime.now(timezone.utc).astimezone(TZ)
    today = now.date()

    news_db = load_json(NEWS_FILE, {"items": []})
    case_db = load_json(CASE_FILE, {"cases": []})
    social_db = load_json(SOCIAL_FILE, {"items": []})

    all_news = news_db.get("items", [])
    all_cases = case_db.get("cases", [])
    all_social = social_db.get("items", [])

    today_news = [item for item in all_news if is_today(item, today)]
    today_jatim = [item for item in today_news if item.get("is_jatim") is True]
    today_outside = [item for item in today_news if item.get("is_jatim") is not True]

    today_social = [item for item in all_social if is_today(item, today)]

    # Cases are active on the day when at least one linked article is collected.
    today_cases_all = [case for case in all_cases if active_case_today(case, today)]
    today_jatim_case_ids = {
        item.get("case_id") for item in today_jatim if item.get("case_id")
    }
    today_jatim_cases = [
        case for case in today_cases_all
        if case.get("case_id") in today_jatim_case_ids
        or case.get("is_jatim") is True
    ]

    def count_scope(items, scope):
        return sum(
            1 for item in items
            if str(item.get("scope") or "").lower() == scope
        )

    def count_priority(items, priority):
        return sum(
            1 for item in items
            if str(item.get("priority") or "").lower() == priority
        )

    negative_jatim = [x for x in today_jatim if str(x.get("scope") or "").lower() == "negative"]
    high_jatim_cases = [
        c for c in today_jatim_cases
        if str(c.get("priority") or "").lower() == "high"
    ]

    snapshot = {
        "schema_version": "today-v3",
        "date": str(today),
        "timezone": "Asia/Jakarta",
        "updated_at": now.isoformat(),
        "last_successful_update": now.isoformat(),

        # Raw daily universe remains available for archive/monitoring.
        "news": {
            "detected": len(today_news),
            "negative": count_scope(today_news, "negative"),
            "positive": count_scope(today_news, "positive"),
            "case": count_scope(today_news, "case"),
            "neutral": count_scope(today_news, "neutral"),
            "jatim": len(today_jatim),
            "luar_jatim": len(today_outside),
            "priority_high": count_priority(today_news, "high"),
            "article_ids": [x.get("id") for x in today_news if x.get("id")],
            "items": today_news,
            "jatim_items": today_jatim,
            "luar_jatim_items": today_outside,
        },

        "cases": {
            "active": len(today_cases_all),
            "priority_high": sum(
                1 for c in today_cases_all
                if str(c.get("priority") or "").lower() == "high"
            ),
            "jatim": len(today_jatim_cases),
            "jatim_priority_high": len(high_jatim_cases),
            "articles": sum(
                int(c.get("article_count", 0) or 0)
                for c in today_cases_all
            ),
            "case_ids": [
                c.get("case_id") for c in today_cases_all if c.get("case_id")
            ],
            "items": today_cases_all,
            "jatim_items": today_jatim_cases,
        },

        "social": {
            "detected": len(today_social),
            "jatim": sum(1 for item in today_social if item.get("is_jatim") is True),
            "negative": count_scope(today_social, "negative"),
            "priority_high": count_priority(today_social, "high"),
            "video_ids": [
                item.get("video_id") for item in today_social if item.get("video_id")
            ],
        },

        # Dashboard-facing Jatim-only aggregates.
        "jatim": {
            "news_today": len(today_jatim),
            "negative_today": len(negative_jatim),
            "positive_today": count_scope(today_jatim, "positive"),
            "case_scope_today": count_scope(today_jatim, "case"),
            "neutral_today": count_scope(today_jatim, "neutral"),
            "case_today": len(today_jatim_cases),
            "case_high_active": len(high_jatim_cases),
            "article_high_today": count_priority(today_jatim, "high"),
            "outside_jatim_today": len(today_outside),
        },

        "regions": build_region_stats(today_jatim),
        "polres": build_polres_stats(today_jatim),
        "categories": build_category_stats(today_jatim),

        "summary": {
            # Legacy/global fields kept for data integrity.
            "news_today": len(today_news),
            "negative_today": count_scope(today_news, "negative"),
            "cases_today": len(today_cases_all),
            "priority_high": sum(
                1 for c in today_cases_all
                if str(c.get("priority") or "").lower() == "high"
            ),
            "article_priority_high": count_priority(today_news, "high"),
            "jatim_news": len(today_jatim),
            # New explicit dashboard metrics.
            "jatim_negative": len(negative_jatim),
            "jatim_positive": count_scope(today_jatim, "positive"),
            "jatim_case_scope": count_scope(today_jatim, "case"),
            "jatim_neutral": count_scope(today_jatim, "neutral"),
            "jatim_cases_today": len(today_jatim_cases),
            "jatim_case_high_active": len(high_jatim_cases),
            "luar_jatim_news": len(today_outside),
            "youtube_today": len(today_social),
        },
    }

    save_json(TODAY_FILE, snapshot)

    archive_path = os.path.join(ARCHIVE_DIR, f"{today}.json")
    save_json(archive_path, snapshot)

    print("========================================")
    print("JAGAT DAILY SNAPSHOT V6.4")
    print("========================================")
    print(f"Tanggal pemantauan : {today}")
    print(f"News today     : {len(today_news)}")
    print(f"Jatim hari ini   : {len(today_jatim)}")
    print(f"Luar Jatim     : {len(today_outside)}")
    print(f"Negative Jatim : {len(negative_jatim)}")
    print(f"Case Jatim     : {len(today_jatim_cases)}")
    print(f"High Case Jatim: {len(high_jatim_cases)}")
    print(f"YouTube        : {len(today_social)}")
    print("----------------------------------------")
    print(f"Today file     : {TODAY_FILE}")
    print(f"Archive        : {archive_path}")
    print("========================================")


if __name__ == "__main__":
    build_snapshot()
