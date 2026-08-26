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
    counter = Counter()
    for item in items:
        if item.get("is_jatim") is True:
            region = item.get("region") or "Jawa Timur"
            location = item.get("polres") or region
            counter[location] += 1
    return [
        {"name": name, "count": count}
        for name, count in counter.most_common()
    ]

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
    today_social = [item for item in all_social if is_today(item, today)]
    today_cases = [case for case in all_cases if active_case_today(case, today)]

    negative_items = [
        item for item in today_news
        if article_is_negative(item)
    ]

    high_cases = [
        case for case in today_cases
        if str(case.get("priority") or "").lower() == "high"
    ]

    snapshot = {
        "schema_version": "today-v2",
        "date": str(today),
        "timezone": "Asia/Jakarta",
        "updated_at": now.isoformat(),
        "last_successful_update": now.isoformat(),

        "news": {
            "detected": len(today_news),
            "negative": len(negative_items),
            "positive": sum(
                1 for item in today_news
                if str(item.get("scope") or "").lower() == "positive"
            ),
            "case": sum(
                1 for item in today_news
                if str(item.get("scope") or "").lower() == "case"
            ),
            "neutral": sum(
                1 for item in today_news
                if str(item.get("scope") or "").lower() == "neutral"
            ),
            "jatim": sum(
                1 for item in today_news
                if item.get("is_jatim") is True
            ),
            "priority_high": sum(
                1 for item in today_news
                if str(item.get("priority") or "").lower() == "high"
            ),
            "article_ids": [
                item.get("id") for item in today_news if item.get("id")
            ],
            "items": today_news,
        },

        "cases": {
            "active": len(today_cases),
            "priority_high": len(high_cases),
            "jatim": sum(
                1 for case in today_cases
                if case.get("is_jatim") is True
            ),
            "articles": sum(
                int(case.get("article_count", 0) or 0)
                for case in today_cases
            ),
            "case_ids": [
                case.get("case_id")
                for case in today_cases
                if case.get("case_id")
            ],
            "items": today_cases,
        },

        "social": {
            "detected": len(today_social),
            "jatim": sum(
                1 for item in today_social
                if item.get("is_jatim") is True
            ),
            "negative": sum(
                1 for item in today_social
                if str(item.get("scope") or "").lower() == "negative"
            ),
            "priority_high": sum(
                1 for item in today_social
                if str(item.get("priority") or "").lower() == "high"
            ),
            "video_ids": [
                item.get("video_id")
                for item in today_social
                if item.get("video_id")
            ],
        },

        "regions": build_region_stats(today_news),
        "polres": build_polres_stats(today_news),
        "categories": build_category_stats(today_news),

        "summary": {
            "news_today": len(today_news),
            "negative_today": len(negative_items),
            "cases_today": len(today_cases),
            "priority_high": len(high_cases),
            "article_priority_high": sum(
                1 for item in today_news
                if str(item.get("priority") or "").lower() == "high"
            ),
            "jatim_news": sum(
                1 for item in today_news
                if item.get("is_jatim") is True
            ),
            "youtube_today": len(today_social),
        },
    }

    save_json(TODAY_FILE, snapshot)

    archive_path = os.path.join(
        ARCHIVE_DIR, f"{today}.json"
    )
    save_json(archive_path, snapshot)

    print("========================================")
    print("PNM DAILY MONITORING SNAPSHOT V2")
    print("========================================")
    print(f"Monitoring date : {today}")
    print(f"Update time     : {now.isoformat()}")
    print("----------------------------------------")
    print(f"News today      : {len(today_news)}")
    print(f"Negative        : {len(negative_items)}")
    print(f"Cases today     : {len(today_cases)}")
    print(f"High cases      : {len(high_cases)}")
    print(f"YouTube         : {len(today_social)}")
    print(f"Jatim news      : {sum(1 for item in today_news if item.get('is_jatim') is True)}")
    print("----------------------------------------")
    print(f"Today file      : {TODAY_FILE}")
    print(f"Archive         : {archive_path}")
    print("========================================")

if __name__ == "__main__":
    build_snapshot()
