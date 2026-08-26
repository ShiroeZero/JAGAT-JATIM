import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# ============================================================
# CONFIG
# ============================================================

NEWS_FILE = "data/news.json"
CASE_FILE = "data/case_clusters.json"
SOCIAL_FILE = "data/social.json"

TODAY_FILE = "data/today.json"
ARCHIVE_DIR = "data/archive"

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


# ============================================================
# HELPERS
# ============================================================

def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception:
        return default


def save_json(path, data):
    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    temp = path + ".tmp"

    with open(
        temp,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temp,
        path
    )


def parse_datetime(value):
    if not value:
        return None

    try:
        text = str(value).replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(text)

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            JAKARTA_TZ
        )

    except Exception:
        return None


# ============================================================
# NEWS
# ============================================================

def build_news_snapshot(news_data, today):
    items = (
        news_data.get("items", [])
        if isinstance(news_data, dict)
        else []
    )

    today_items = []

    for item in items:

        if not isinstance(item, dict):
            continue

        published = parse_datetime(
            item.get("published_at")
        )

        collected = parse_datetime(
            item.get("collected_at")
        )

        # Detected today takes priority.
        reference_time = (
            collected
            or published
        )

        if not reference_time:
            continue

        if reference_time.date() != today:
            continue

        today_items.append(item)

    negative = 0
    positive = 0
    neutral = 0
    jatim = 0
    high_priority = 0

    for item in today_items:

        category = str(
            item.get(
                "category",
                ""
            )
        ).lower()

        scope = str(
            item.get(
                "scope",
                ""
            )
        ).lower()

        priority = str(
            item.get(
                "priority",
                ""
            )
        ).lower()

        if (
            scope == "negative"
            or "negative" in category
            or "oknum" in category
        ):
            negative += 1

        elif (
            scope == "positive"
            or "positive" in category
        ):
            positive += 1

        else:
            neutral += 1

        if item.get("is_jatim") is True:
            jatim += 1

        if priority == "high":
            high_priority += 1

    return {
        "detected": len(today_items),
        "negative": negative,
        "positive": positive,
        "neutral": neutral,
        "jatim": jatim,
        "priority_high": high_priority,
        "article_ids": [
            item.get("id")
            for item in today_items
            if item.get("id")
        ]
    }


# ============================================================
# CASES
# ============================================================

def build_case_snapshot(case_data, today):
    cases = (
        case_data.get("cases", [])
        if isinstance(case_data, dict)
        else []
    )

    active_today = []
    priority_high = 0
    jatim = 0
    articles = 0

    for case in cases:

        if not isinstance(case, dict):
            continue

        first_seen = parse_datetime(
            case.get("first_seen")
        )

        last_seen = parse_datetime(
            case.get("last_seen")
        )

        # Case is considered active today if:
        # - first seen today
        # OR
        # - latest article/update is today
        if not (
            (
                first_seen
                and first_seen.date() == today
            )
            or
            (
                last_seen
                and last_seen.date() == today
            )
        ):
            continue

        active_today.append(case)

        articles += int(
            case.get(
                "article_count",
                0
            )
            or 0
        )

        if str(
            case.get(
                "priority",
                ""
            )
        ).lower() == "high":

            priority_high += 1

        if case.get(
            "is_jatim"
        ) is True:

            jatim += 1

    return {
        "active": len(active_today),
        "priority_high": priority_high,
        "jatim": jatim,
        "articles": articles,
        "case_ids": [
            case.get("case_id")
            for case in active_today
            if case.get("case_id")
        ]
    }


# ============================================================
# YOUTUBE
# ============================================================

def build_social_snapshot(
    social_data,
    today
):
    items = (
        social_data.get("items", [])
        if isinstance(social_data, dict)
        else []
    )

    today_items = []

    for item in items:

        if not isinstance(item, dict):
            continue

        collected = parse_datetime(
            item.get("collected_at")
        )

        published = parse_datetime(
            item.get("published_at")
        )

        reference_time = (
            collected
            or published
        )

        if not reference_time:
            continue

        if reference_time.date() != today:
            continue

        today_items.append(item)

    jatim = sum(
        1
        for item in today_items
        if item.get("is_jatim") is True
    )

    high = sum(
        1
        for item in today_items
        if str(
            item.get(
                "priority",
                ""
            )
        ).lower() == "high"
    )

    negative = sum(
        1
        for item in today_items
        if str(
            item.get(
                "scope",
                ""
            )
        ).lower() == "negative"
    )

    return {
        "detected": len(today_items),
        "jatim": jatim,
        "negative": negative,
        "priority_high": high,
        "video_ids": [
            item.get("video_id")
            for item in today_items
            if item.get("video_id")
        ]
    }


# ============================================================
# MAIN
# ============================================================

def main():

    now = datetime.now(
        timezone.utc
    ).astimezone(
        JAKARTA_TZ
    )

    today = now.date()

    print(
        "========================================"
    )
    print(
        "PNM DAILY MONITORING SNAPSHOT"
    )
    print(
        "========================================"
    )

    print(
        f"Monitoring date : {today}"
    )

    print(
        f"Update time     : "
        f"{now.isoformat()}"
    )

    news_data = load_json(
        NEWS_FILE,
        {}
    )

    case_data = load_json(
        CASE_FILE,
        {}
    )

    social_data = load_json(
        SOCIAL_FILE,
        {}
    )

    news_snapshot = build_news_snapshot(
        news_data,
        today
    )

    case_snapshot = build_case_snapshot(
        case_data,
        today
    )

    social_snapshot = build_social_snapshot(
        social_data,
        today
    )

    snapshot = {

        "date":
            str(today),

        "timezone":
            "Asia/Jakarta",

        "updated_at":
            now.isoformat(),

        "last_successful_update":
            now.isoformat(),

        "news":
            news_snapshot,

        "cases":
            case_snapshot,

        "social":
            social_snapshot,

        "summary": {

            "news_today":
                news_snapshot[
                    "detected"
                ],

            "negative_today":
                news_snapshot[
                    "negative"
                ],

            "cases_today":
                case_snapshot[
                    "active"
                ],

            "priority_high":
                (
                    news_snapshot[
                        "priority_high"
                    ]
                    +
                    case_snapshot[
                        "priority_high"
                    ]
                ),

            "jatim_news":
                news_snapshot[
                    "jatim"
                ],

            "youtube_today":
                social_snapshot[
                    "detected"
                ]

        }
    }

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    save_json(
        TODAY_FILE,
        snapshot
    )

    # --------------------------------------------------------
    # ARCHIVE
    # --------------------------------------------------------

    archive_file = os.path.join(
        ARCHIVE_DIR,
        f"{today}.json"
    )

    save_json(
        archive_file,
        snapshot
    )

    print(
        "========================================"
    )

    print(
        "SNAPSHOT COMPLETE"
    )

    print(
        f"Today file : {TODAY_FILE}"
    )

    print(
        f"Archive    : {archive_file}"
    )

    print(
        f"News       : "
        f"{news_snapshot['detected']}"
    )

    print(
        f"Cases      : "
        f"{case_snapshot['active']}"
    )

    print(
        f"YouTube    : "
        f"{social_snapshot['detected']}"
    )

    print(
        f"Jatim      : "
        f"{news_snapshot['jatim']}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
