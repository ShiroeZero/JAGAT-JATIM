import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = {
    "news": os.path.join(BASE, "data", "news.json"),
    "cases": os.path.join(BASE, "data", "case_clusters.json"),
    "today": os.path.join(BASE, "data", "today.json"),
}

TZ = ZoneInfo("Asia/Jakarta")


# ============================================================
# BASIC HELPERS
# ============================================================

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
    """
    Gunakan tanggal publikasi sebagai sumber utama.
    collected_at hanya fallback jika published_at tidak tersedia.
    """
    dt = parse_dt(
        item.get("published_at")
        or item.get("collected_at")
    )

    return bool(
        dt
        and dt.date() == date_value
    )


def priority_for_score(score, severity=0):
    score = int(score or 0)
    severity = int(severity or 0)

    if severity >= 40 or (
        score >= 65
        and severity >= 25
    ):
        return "high"

    if score >= 40:
        return "medium"

    return "low"


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    # --------------------------------------------------------
    # FILE EXISTENCE
    # --------------------------------------------------------

    for name, path in FILES.items():
        if not os.path.exists(path):
            fail(
                f"{name} file missing: {path}"
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

    news = news_db.get(
        "items",
        []
    )

    cases = case_db.get(
        "cases",
        []
    )

    errors = []


    # ========================================================
    # ID INTEGRITY
    # ========================================================

    news_ids = [
        x.get("id")
        for x in news
        if x.get("id")
    ]

    case_ids = [
        x.get("case_id")
        for x in cases
        if x.get("case_id")
    ]

    if len(news_ids) != len(set(news_ids)):
        errors.append(
            "Duplicate news IDs detected"
        )

    if len(case_ids) != len(set(case_ids)):
        errors.append(
            "Duplicate case IDs detected"
        )

    news_map = {
        x["id"]: x
        for x in news
        if x.get("id")
    }

    case_map = {
        x["case_id"]: x
        for x in cases
        if x.get("case_id")
    }


    # ========================================================
    # NEWS → CASE RELATIONSHIP
    # ========================================================

    seen_case_articles = set()

    for item in news:

        cid = item.get(
            "case_id"
        )

        if cid and cid not in case_map:
            errors.append(
                f"news {item.get('id')} "
                f"points to missing {cid}"
            )


    # ========================================================
    # CASE → NEWS RELATIONSHIP
    # ========================================================

    for case in cases:

        cid = case.get(
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


        # ----------------------------------------------------
        # Duplicate article IDs inside Case
        # ----------------------------------------------------

        if len(article_ids) != len(
            set(article_ids)
        ):
            errors.append(
                f"{cid} has duplicate article_ids"
            )


        # ----------------------------------------------------
        # article_ids ↔ articles[]
        # ----------------------------------------------------

        object_ids = [
            a.get("id")
            for a in article_objects
            if a.get("id")
        ]

        if set(object_ids) != set(article_ids):
            errors.append(
                f"{cid} article_ids/articles mismatch"
            )


        # ----------------------------------------------------
        # Reverse relationship
        # ----------------------------------------------------

        for aid in article_ids:

            if aid not in news_map:

                errors.append(
                    f"{cid} points to missing article {aid}"
                )

            else:

                news_case_id = (
                    news_map[aid].get(
                        "case_id"
                    )
                )

                if news_case_id != cid:

                    errors.append(
                        f"{cid}/{aid} "
                        f"reverse link mismatch: "
                        f"news.case_id={news_case_id}"
                    )


            # ------------------------------------------------
            # One article must not exist in two cases
            # ------------------------------------------------

            if aid in seen_case_articles:

                errors.append(
                    f"article {aid} appears in multiple cases"
                )

            seen_case_articles.add(
                aid
            )


        # ====================================================
        # CASE PRIORITY VALIDATION
        # ====================================================

        breakdown = (
            case.get(
                "priority_breakdown"
            )
            or {}
        )

        score = case.get(
            "priority_score"
        )

        if score is None:

            errors.append(
                f"{cid} missing priority_score"
            )

        else:

            expected_score = sum(
                int(
                    breakdown.get(
                        key
                    )
                    or 0
                )
                for key in (
                    "severity",
                    "escalation",
                    "spread",
                    "current_activity",
                )
            )

            if int(score) != expected_score:

                errors.append(
                    f"{cid} priority_score mismatch: "
                    f"stored={score}, "
                    f"expected={expected_score}"
                )


            expected_priority = (
                priority_for_score(
                    score,
                    breakdown.get(
                        "severity",
                        0
                    )
                )
            )

            actual_priority = str(
                case.get(
                    "priority"
                )
                or "low"
            ).lower()

            if actual_priority != expected_priority:

                errors.append(
                    f"{cid} priority mismatch: "
                    f"stored={actual_priority}, "
                    f"expected={expected_priority}"
                )


    # ========================================================
    # TODAY DATE
    # ========================================================

    date_value = today_db.get(
        "date"
    )

    if not date_value:
        fail(
            "today.json missing date"
        )

    try:

        today = datetime.strptime(
            str(date_value),
            "%Y-%m-%d"
        ).date()

    except ValueError:

        fail(
            f"Invalid today date: {date_value}"
        )


    # ========================================================
    # RAW NEWS TODAY
    # ========================================================

    actual_today = [
        x
        for x in news
        if is_today(
            x,
            today
        )
    ]

    actual_news_count = (
        len(actual_today)
    )

    actual_negative = sum(
        1
        for x in actual_today
        if str(
            x.get("scope")
            or ""
        ).lower()
        == "negative"
    )

    actual_positive = sum(
        1
        for x in actual_today
        if str(
            x.get("scope")
            or ""
        ).lower()
        == "positive"
    )

    actual_case_scope = sum(
        1
        for x in actual_today
        if str(
            x.get("scope")
            or ""
        ).lower()
        == "case"
    )

    actual_neutral = sum(
        1
        for x in actual_today
        if str(
            x.get("scope")
            or ""
        ).lower()
        == "neutral"
    )


    # ========================================================
    # JAWA TIMUR TODAY
    # ========================================================

    actual_jatim_items = [
        x
        for x in actual_today
        if x.get("is_jatim") is True
    ]

    actual_jatim = (
        len(
            actual_jatim_items
        )
    )


    actual_jatim_negative = sum(
        1
        for x in actual_jatim_items
        if str(
            x.get("scope")
            or ""
        ).lower()
        == "negative"
    )


    # ========================================================
    # ARTICLE PRIORITY
    # ========================================================

    actual_article_high = sum(
        1
        for x in actual_today
        if str(
            x.get("priority")
            or ""
        ).lower()
        == "high"
    )


    # ========================================================
    # CASE ACTIVITY TODAY
    #
    # IMPORTANT:
    #
    # Case tetap tersimpan dan tetap memiliki priority.
    #
    # Tetapi Case hanya dihitung sebagai "aktif hari ini"
    # apabila memiliki artikel yang terbit pada tanggal today.
    #
    # Jadi:
    #
    # CASE TUBAN 26 AGUSTUS
    # → tetap HIGH di database
    # → tidak otomatis menjadi HIGH TODAY pada 27 AGUSTUS
    # ========================================================

    active_today_cases = [
        case
        for case in cases
        if any(
            is_today(
                article,
                today
            )
            for article in (
                case.get(
                    "articles",
                    []
                )
            )
        )
    ]


    # ========================================================
    # GLOBAL CASE HIGH TODAY
    # ========================================================

    actual_case_high_global = sum(
        1
        for case in active_today_cases
        if str(
            case.get("priority")
            or ""
        ).lower()
        == "high"
    )


    # ========================================================
    # JAWA TIMUR CASES TODAY
    # ========================================================

    active_today_jatim_cases = [
        case
        for case in active_today_cases
        if case.get("is_jatim") is True
    ]


    # ========================================================
    # JAWA TIMUR CASE HIGH TODAY
    # ========================================================

    actual_case_high_jatim = sum(
        1
        for case in active_today_jatim_cases
        if str(
            case.get("priority")
            or ""
        ).lower()
        == "high"
    )


    # ========================================================
    # TODAY SUMMARY STORED
    # ========================================================

    today_summary = (
        today_db.get(
            "summary",
            {}
        )
    )


    stored_news = int(
        today_summary.get(
            "news_today",
            0
        )
        or 0
    )

    stored_negative = int(
        today_summary.get(
            "negative_today",
            0
        )
        or 0
    )

    stored_jatim = int(
        today_summary.get(
            "jatim_news",
            0
        )
        or 0
    )

    stored_case_high_global = int(
        today_summary.get(
            "priority_high",
            0
        )
        or 0
    )

    stored_article_high = int(
        today_summary.get(
            "article_priority_high",
            today_db.get(
                "news",
                {}
            ).get(
                "priority_high",
                0
            )
        )
        or 0
    )


    # ========================================================
    # GLOBAL CHECKS
    # ========================================================

    checks = [

        (
            stored_news,
            actual_news_count,
            "today.json news count"
        ),

        (
            stored_negative,
            actual_negative,
            "today.json negative count"
        ),

        (
            stored_jatim,
            actual_jatim,
            "today.json Jatim count"
        ),

        (
            stored_case_high_global,
            actual_case_high_global,
            "today.json global case-high count"
        ),

        (
            stored_article_high,
            actual_article_high,
            "today.json article-high count"
        ),
    ]


    # ========================================================
    # JAWA TIMUR DASHBOARD CHECKS
    # ========================================================

    jatim_db = (
        today_db.get(
            "jatim",
            {}
        )
    )


    stored_jatim_news = int(
        jatim_db.get(
            "news_today",
            0
        )
        or 0
    )


    stored_jatim_negative = int(
        jatim_db.get(
            "negative_today",
            0
        )
        or 0
    )


    stored_jatim_case_high = int(
        jatim_db.get(
            "case_high_active",
            0
        )
        or 0
    )


    checks.extend([

        (
            stored_jatim_news,
            actual_jatim,
            "today.json Jatim dashboard news count"
        ),

        (
            stored_jatim_negative,
            actual_jatim_negative,
            "today.json Jatim negative count"
        ),

        (
            stored_jatim_case_high,
            actual_case_high_jatim,
            "today.json Jatim case-high count"
        ),

    ])


    # ========================================================
    # RUN CHECKS
    # ========================================================

    for stored, actual, label in checks:

        if stored != actual:

            errors.append(
                f"{label} mismatch: "
                f"stored={stored}, "
                f"actual={actual}"
            )


    # ========================================================
    # TODAY ARTICLE IDS
    # ========================================================

    stored_article_ids = set(
        today_db.get(
            "news",
            {}
        ).get(
            "article_ids",
            []
        )
    )

    actual_article_ids = {
        x.get("id")
        for x in actual_today
        if x.get("id")
    }


    if stored_article_ids != actual_article_ids:

        errors.append(
            "today.json article_ids "
            "do not match raw news.json"
        )


    # ========================================================
    # ERROR OUTPUT
    # ========================================================

    if errors:

        for error in errors[:50]:
            print(
                "ERROR:",
                error
            )

        fail(
            f"validation failed with "
            f"{len(errors)} issue(s)"
        )


    # ========================================================
    # SUCCESS OUTPUT
    # ========================================================

    print(
        "========================================"
    )

    print(
        "JAGAT SYSTEM DATA VALIDATION V6.4"
    )

    print(
        "========================================"
    )

    print(
        f"News records          : {len(news)}"
    )

    print(
        f"Case records          : {len(cases)}"
    )

    print(
        f"Case links            : {len(seen_case_articles)}"
    )

    print(
        f"Today date            : {today}"
    )

    print(
        f"Actual news today     : {actual_news_count}"
    )

    print(
        f"Stored news today     : {stored_news}"
    )

    print(
        f"Negative today        : {actual_negative}"
    )

    print(
        f"Positive today        : {actual_positive}"
    )

    print(
        f"Case scope today      : {actual_case_scope}"
    )

    print(
        f"Neutral today         : {actual_neutral}"
    )

    print(
        f"Jatim today           : {actual_jatim}"
    )

    print(
        f"Jatim negative        : {actual_jatim_negative}"
    )

    print(
        f"Global case high today: {actual_case_high_global}"
    )

    print(
        f"Jatim case high today : {actual_case_high_jatim}"
    )

    print(
        f"Article high today    : {actual_article_high}"
    )

    print(
        "----------------------------------------"
    )

    print(
        "Consistency            : OK"
    )

    print(
        "Today snapshot         : OK"
    )

    print(
        "Global/Jatim scope     : OK"
    )

    print(
        "Case relationships     : OK"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
