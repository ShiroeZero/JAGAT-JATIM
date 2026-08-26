import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FILES = {
    "news": os.path.join(
        BASE,
        "data",
        "news.json",
    ),
    "cases": os.path.join(
        BASE,
        "data",
        "case_clusters.json",
    ),
    "today": os.path.join(
        BASE,
        "data",
        "today.json",
    ),
}


JAKARTA_TZ = ZoneInfo(
    "Asia/Jakarta"
)


def load(path):
    with open(
        path,
        encoding="utf-8",
    ) as f:
        return json.load(f)


def fail(message):
    print(
        f"ERROR: {message}"
    )
    raise SystemExit(1)


def parse_dt(value):
    if not value:
        return None

    try:
        text = str(
            value
        ).replace(
            "Z",
            "+00:00",
        )

        dt = datetime.fromisoformat(
            text
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            JAKARTA_TZ
        )

    except Exception:
        return None


def is_detected_today(
    item,
    today,
):
    """
    Hari monitoring ditentukan dari waktu
    COLLECTED / DETECTED.

    published_at hanya menjadi fallback
    apabila collected_at tidak tersedia.
    """

    collected = parse_dt(
        item.get(
            "collected_at"
        )
    )

    published = parse_dt(
        item.get(
            "published_at"
        )
    )

    reference = (
        collected
        or published
    )

    if not reference:
        return False

    return (
        reference.date()
        == today
    )


def priority_rank(value):
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
    }.get(
        str(
            value
            or "low"
        ).lower(),
        1,
    )


def main():

    for name, path in FILES.items():

        if not os.path.exists(path):
            fail(
                f"{name} file missing: "
                f"{path}"
            )

    news_db = load(
        FILES["news"]
    )

    case_db = load(
        FILES["cases"]
    )

    today_db = load(
        FILES["today"]
    )

    news = (
        news_db.get(
            "items",
            []
        )
        if isinstance(
            news_db,
            dict
        )
        else []
    )

    cases = (
        case_db.get(
            "cases",
            []
        )
        if isinstance(
            case_db,
            dict
        )
        else []
    )

    errors = []

    # ========================================================
    # 1. NEWS ID VALIDATION
    # ========================================================

    news_ids = [
        item.get("id")
        for item in news
        if item.get("id")
    ]

    if len(news_ids) != len(
        set(news_ids)
    ):
        errors.append(
            "Duplicate news IDs detected"
        )


    # ========================================================
    # 2. CASE ID VALIDATION
    # ========================================================

    case_ids = [
        case.get("case_id")
        for case in cases
        if case.get("case_id")
    ]

    if len(case_ids) != len(
        set(case_ids)
    ):
        errors.append(
            "Duplicate case IDs detected"
        )


    case_map = {
        case["case_id"]: case
        for case in cases
        if case.get("case_id")
    }

    news_map = {
        item["id"]: item
        for item in news
        if item.get("id")
    }


    # ========================================================
    # 3. NEWS → CASE
    # ========================================================

    for item in news:

        case_id = item.get(
            "case_id"
        )

        if (
            case_id
            and case_id not in case_map
        ):
            errors.append(
                "news "
                f"{item.get('id')} "
                f"points to missing "
                f"{case_id}"
            )


    # ========================================================
    # 4. CASE → ARTICLES
    # ========================================================

    seen_case_articles = set()

    for case in cases:

        case_id = case.get(
            "case_id"
        )

        article_ids = (
            case.get(
                "article_ids",
                []
            )
        )

        article_objects = (
            case.get(
                "articles",
                []
            )
        )

        # Duplicate IDs inside one Case
        if len(
            article_ids
        ) != len(
            set(article_ids)
        ):
            errors.append(
                f"{case_id} has "
                "duplicate article_ids"
            )

        object_ids = [
            article.get("id")
            for article
            in article_objects
            if article.get("id")
        ]

        # article_ids and articles must match
        if set(
            object_ids
        ) != set(
            article_ids
        ):
            errors.append(
                f"{case_id} "
                "article_ids/articles mismatch"
            )

        for article_id in article_ids:

            # Article must exist in news DB
            if article_id not in news_map:

                errors.append(
                    f"{case_id} points to "
                    f"missing article "
                    f"{article_id}"
                )

            else:

                # Reverse relationship
                reverse_case_id = (
                    news_map[
                        article_id
                    ].get(
                        "case_id"
                    )
                )

                if reverse_case_id != case_id:

                    errors.append(
                        f"{case_id}/"
                        f"{article_id} "
                        "reverse link mismatch: "
                        f"news.case_id="
                        f"{reverse_case_id}"
                    )

            # One article may not belong
            # to more than one case.
            if (
                article_id
                in seen_case_articles
            ):

                errors.append(
                    f"article "
                    f"{article_id} "
                    "appears in multiple cases"
                )

            seen_case_articles.add(
                article_id
            )


        # ====================================================
        # 5. CANONICAL CASE PRIORITY
        # ====================================================

        priorities = [
            priority_rank(
                article.get(
                    "priority"
                )
            )
            for article
            in article_objects
        ]

        if priorities:

            expected = max(
                priorities
            )

            actual = priority_rank(
                case.get(
                    "priority"
                )
            )

            if actual != expected:

                errors.append(
                    f"{case_id} "
                    "priority is not "
                    "canonical from articles"
                )


    # ========================================================
    # 6. RE-CALCULATE TODAY FROM RAW NEWS
    # ========================================================

    today_value = today_db.get(
        "date"
    )

    if not today_value:
        fail(
            "today.json does not contain date"
        )

    try:
        today = datetime.strptime(
            str(today_value),
            "%Y-%m-%d",
        ).date()

    except ValueError:
        fail(
            "today.json contains invalid date: "
            f"{today_value}"
        )


    actual_today_items = [
        item
        for item in news
        if is_detected_today(
            item,
            today,
        )
    ]


    # ========================================================
    # 7. TODAY METRIC CALCULATION
    # ========================================================

    actual_today_count = len(
        actual_today_items
    )

    actual_negative = sum(
        1
        for item
        in actual_today_items
        if str(
            item.get(
                "scope"
            )
            or ""
        ).lower()
        == "negative"
    )

    actual_positive = sum(
        1
        for item
        in actual_today_items
        if str(
            item.get(
                "scope"
            )
            or ""
        ).lower()
        == "positive"
    )

    actual_case = sum(
        1
        for item
        in actual_today_items
        if str(
            item.get(
                "scope"
            )
            or ""
        ).lower()
        == "case"
    )

    actual_neutral = sum(
        1
        for item
        in actual_today_items
        if str(
            item.get(
                "scope"
            )
            or ""
        ).lower()
        == "neutral"
    )

    actual_jatim = sum(
        1
        for item
        in actual_today_items
        if item.get(
            "is_jatim"
        )
        is True
    )

    actual_high = sum(
        1
        for item
        in actual_today_items
        if str(
            item.get(
                "priority"
            )
            or ""
        ).lower()
        == "high"
    )


    # ========================================================
    # 8. TODAY.JSON MUST MATCH RAW NEWS
    # ========================================================

    today_news = (
        today_db.get(
            "news",
            {}
        )
        if isinstance(
            today_db,
            dict
        )
        else {}
    )

    today_summary = (
        today_db.get(
            "summary",
            {}
        )
        if isinstance(
            today_db,
            dict
        )
        else {}
    )


    stored_today_count = int(
        today_summary.get(
            "news_today",
            today_news.get(
                "detected",
                0
            ),
        )
        or 0
    )

    stored_negative = int(
        today_summary.get(
            "negative_today",
            today_news.get(
                "negative",
                0
            ),
        )
        or 0
    )

    stored_jatim = int(
        today_summary.get(
            "jatim_news",
            today_news.get(
                "jatim",
                0
            ),
        )
        or 0
    )

    stored_high = int(
        today_summary.get(
            "priority_high",
            today_news.get(
                "priority_high",
                0
            ),
        )
        or 0
    )


    if (
        stored_today_count
        != actual_today_count
    ):

        errors.append(
            "today.json news count "
            "does not match raw news.json: "
            f"stored={stored_today_count}, "
            f"actual={actual_today_count}"
        )


    if (
        stored_negative
        != actual_negative
    ):

        errors.append(
            "today.json negative count "
            "does not match raw news.json: "
            f"stored={stored_negative}, "
            f"actual={actual_negative}"
        )


    if (
        stored_jatim
        != actual_jatim
    ):

        errors.append(
            "today.json Jatim count "
            "does not match raw news.json: "
            f"stored={stored_jatim}, "
            f"actual={actual_jatim}"
        )


    if (
        stored_high
        != actual_high
    ):

        errors.append(
            "today.json high-priority "
            "count does not match "
            "raw news.json: "
            f"stored={stored_high}, "
            f"actual={actual_high}"
        )


    # ========================================================
    # 9. TODAY ARTICLE IDS
    # ========================================================

    stored_article_ids = set(
        today_news.get(
            "article_ids",
            []
        )
    )

    actual_article_ids = {
        item.get("id")
        for item
        in actual_today_items
        if item.get("id")
    }

    if (
        stored_article_ids
        != actual_article_ids
    ):

        errors.append(
            "today.json article_ids "
            "do not match raw "
            "news.json"
        )


    # ========================================================
    # 10. RESULT
    # ========================================================

    print(
        "========================================"
    )

    print(
        "PNM SYSTEM DATA VALIDATION"
    )

    print(
        "========================================"
    )

    print(
        f"News records        : {len(news)}"
    )

    print(
        f"Case records        : {len(cases)}"
    )

    print(
        f"Case links          : "
        f"{len(seen_case_articles)}"
    )

    print(
        f"Today date          : {today}"
    )

    print(
        f"Actual news today   : "
        f"{actual_today_count}"
    )

    print(
        f"Stored news today   : "
        f"{stored_today_count}"
    )

    print(
        f"Negative today      : "
        f"{actual_negative}"
    )

    print(
        f"Positive today      : "
        f"{actual_positive}"
    )

    print(
        f"Case scope today    : "
        f"{actual_case}"
    )

    print(
        f"Neutral today       : "
        f"{actual_neutral}"
    )

    print(
        f"Jatim today         : "
        f"{actual_jatim}"
    )

    print(
        f"High priority today : "
        f"{actual_high}"
    )

    print(
        "========================================"
    )

    if errors:

        for error in errors[:50]:

            print(
                "ERROR:",
                error
            )

        print(
            "========================================"
        )

        fail(
            "validation failed with "
            f"{len(errors)} issue(s)"
        )

    print(
        "Consistency         : OK"
    )

    print(
        "Today snapshot      : OK"
    )

    print(
        "Case relationships   : OK"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
