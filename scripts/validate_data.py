import json
import os
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
        "news.json"
    ),
    "cases": os.path.join(
        BASE,
        "data",
        "case_clusters.json"
    ),
    "today": os.path.join(
        BASE,
        "data",
        "today.json"
    ),
}

TZ = ZoneInfo(
    "Asia/Jakarta"
)


# ============================================================
# LOAD
# ============================================================

def load_json(path):
    with open(
        path,
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# DATE
# ============================================================

def parse_dt(value):
    if not value:
        return None

    try:
        text = str(
            value
        ).replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            text
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            TZ
        )

    except Exception:
        return None


def monitoring_date(item):
    """
    KONTRAK TANGGAL JAGAT

    Monitoring "hari ini" menggunakan:
        1. collected_at
        2. published_at sebagai fallback

    Alasannya:
    JAGAT adalah sistem monitoring.
    Berita yang baru ditemukan/dikumpulkan hari ini
    harus masuk snapshot hari ini walaupun artikel tersebut
    dipublikasikan sebelumnya.
    """
    return (
        parse_dt(
            item.get(
                "collected_at"
            )
        )
        or
        parse_dt(
            item.get(
                "published_at"
            )
        )
    )


def is_today(
    item,
    today
):
    dt = monitoring_date(
        item
    )

    return bool(
        dt
        and dt.date() == today
    )


# ============================================================
# PRIORITY
# ============================================================

def priority_value(value):
    return str(
        value or ""
    ).strip().lower()


# ============================================================
# FILE EXISTENCE
# ============================================================

def validate_files():

    for name, path in FILES.items():

        if not os.path.exists(
            path
        ):
            raise RuntimeError(
                f"{name} file missing: {path}"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    validate_files()

    news_db = load_json(
        FILES["news"]
    )

    case_db = load_json(
        FILES["cases"]
    )

    today_db = load_json(
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
    # NEWS IDS
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


    news_map = {
        item["id"]: item
        for item in news
        if item.get("id")
    }


    # ========================================================
    # CASE IDS
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


    # ========================================================
    # NEWS → CASE
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
                f"news {item.get('id')} "
                f"points to missing {case_id}"
            )


    # ========================================================
    # CASE → NEWS
    # ========================================================

    seen_article_case = {}

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


        # ----------------------------------------------------
        # Duplicate article IDs
        # ----------------------------------------------------

        if len(
            article_ids
        ) != len(
            set(article_ids)
        ):

            errors.append(
                f"{case_id} has duplicate article_ids"
            )


        # ----------------------------------------------------
        # Compact article objects
        # ----------------------------------------------------

        object_ids = {
            article.get("id")
            for article in article_objects
            if article.get("id")
        }

        if object_ids != set(
            article_ids
        ):

            errors.append(
                f"{case_id} article_ids/articles mismatch"
            )


        # ----------------------------------------------------
        # Verify article existence
        # ----------------------------------------------------

        for article_id in article_ids:

            if article_id not in news_map:

                errors.append(
                    f"{case_id} "
                    f"points to missing article "
                    f"{article_id}"
                )

                continue


            news_case_id = (
                news_map[
                    article_id
                ].get(
                    "case_id"
                )
            )

            if news_case_id != case_id:

                errors.append(
                    f"{case_id}/{article_id} "
                    f"reverse relationship mismatch: "
                    f"news.case_id={news_case_id}"
                )


            # ------------------------------------------------
            # An article must belong to one Case only.
            # ------------------------------------------------

            previous = seen_article_case.get(
                article_id
            )

            if (
                previous
                and previous != case_id
            ):

                errors.append(
                    f"article {article_id} "
                    f"appears in multiple cases: "
                    f"{previous}, {case_id}"
                )

            seen_article_case[
                article_id
            ] = case_id


    # ========================================================
    # TODAY DATE
    # ========================================================

    today_text = today_db.get(
        "date"
    )

    if not today_text:

        raise RuntimeError(
            "today.json missing date"
        )


    try:

        today = datetime.strptime(
            str(today_text),
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise RuntimeError(
            f"Invalid today date: {today_text}"
        )


    # ========================================================
    # ACTUAL NEWS TODAY
    # ========================================================

    actual_today = [
        item
        for item in news
        if is_today(
            item,
            today
        )
    ]


    actual_news_count = len(
        actual_today
    )


    # ========================================================
    # GLOBAL ARTICLE COUNTS
    # ========================================================

    actual_negative = sum(
        1
        for item in actual_today
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "negative"
    )


    actual_positive = sum(
        1
        for item in actual_today
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "positive"
    )


    actual_case_scope = sum(
        1
        for item in actual_today
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "case"
    )


    actual_neutral = sum(
        1
        for item in actual_today
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "neutral"
    )


    actual_article_high = sum(
        1
        for item in actual_today
        if priority_value(
            item.get(
                "priority"
            )
        )
        == "high"
    )


    # ========================================================
    # JAWA TIMUR
    # ========================================================

    actual_jatim = [
        item
        for item in actual_today
        if item.get(
            "is_jatim"
        ) is True
    ]


    actual_jatim_count = len(
        actual_jatim
    )


    actual_jatim_negative = sum(
        1
        for item in actual_jatim
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "negative"
    )


    actual_jatim_positive = sum(
        1
        for item in actual_jatim
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "positive"
    )


    actual_jatim_case_scope = sum(
        1
        for item in actual_jatim
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "case"
    )


    actual_jatim_neutral = sum(
        1
        for item in actual_jatim
        if str(
            item.get("scope")
            or ""
        ).lower()
        == "neutral"
    )


    # ========================================================
    # ACTIVE CASE TODAY
    #
    # CASE PRIORITY TETAP.
    #
    # Tetapi CASE hanya dianggap "aktif hari ini"
    # jika minimal satu artikel di dalam Case
    # terdeteksi/dikumpulkan hari ini.
    # ========================================================

    active_today_cases = []

    for case in cases:

        articles = (
            case.get(
                "articles",
                []
            )
        )

        if any(
            is_today(
                article,
                today
            )
            for article in articles
        ):

            active_today_cases.append(
                case
            )


    # ========================================================
    # GLOBAL CASE HIGH
    # ========================================================

    actual_case_high_global = sum(
        1
        for case in active_today_cases
        if priority_value(
            case.get(
                "priority"
            )
        )
        == "high"
    )


    # ========================================================
    # JATIM ACTIVE CASE
    # ========================================================

    active_today_jatim_cases = [
        case
        for case in active_today_cases
        if case.get(
            "is_jatim"
        ) is True
    ]


    actual_case_high_jatim = sum(
        1
        for case in active_today_jatim_cases
        if priority_value(
            case.get(
                "priority"
            )
        )
        == "high"
    )


    # ========================================================
    # STORED SUMMARY
    # ========================================================

    summary = today_db.get(
        "summary",
        {}
    )

    stored_news = int(
        summary.get(
            "news_today",
            0
        )
        or 0
    )


    stored_negative = int(
        summary.get(
            "negative_today",
            0
        )
        or 0
    )


    stored_jatim = int(
        summary.get(
            "jatim_news",
            0
        )
        or 0
    )


    stored_global_case_high = int(
        summary.get(
            "priority_high",
            0
        )
        or 0
    )


    stored_article_high = int(
        summary.get(
            "article_priority_high",
            0
        )
        or 0
    )


    # ========================================================
    # STORED JATIM
    # ========================================================

    jatim_db = today_db.get(
        "jatim",
        {}
    )


    stored_jatim_dashboard_news = int(
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


    # ========================================================
    # GLOBAL VALIDATION
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
            actual_jatim_count,
            "today.json Jatim count"
        ),

        (
            stored_global_case_high,
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
    # JATIM VALIDATION
    # ========================================================

    jatim_checks = [

        (
            stored_jatim_dashboard_news,
            actual_jatim_count,
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

    ]


    checks.extend(
        jatim_checks
    )


    # ========================================================
    # ARTICLE IDS
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
        item.get("id")
        for item in actual_today
        if item.get("id")
    }


    if (
        stored_article_ids
        != actual_article_ids
    ):

        missing_from_snapshot = (
            actual_article_ids
            - stored_article_ids
        )

        extra_in_snapshot = (
            stored_article_ids
            - actual_article_ids
        )

        errors.append(
            "today.json article_ids do not match "
            "news.json using monitoring date "
            f"(missing={len(missing_from_snapshot)}, "
            f"extra={len(extra_in_snapshot)})"
        )


    # ========================================================
    # TODAY JATIM ITEMS
    # ========================================================

    stored_jatim_items = {
        item.get("id")
        for item in today_db.get(
            "news",
            {}
        ).get(
            "jatim_items",
            []
        )
        if item.get("id")
    }


    actual_jatim_ids = {
        item.get("id")
        for item in actual_jatim
        if item.get("id")
    }


    if (
        stored_jatim_items
        != actual_jatim_ids
    ):

        errors.append(
            "today.json Jatim items do not match "
            "news.json monitoring date"
        )


    # ========================================================
    # RESULT
    # ========================================================

    if errors:

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
            f"Monitoring date       : {today}"
        )

        print(
            f"Actual news today     : {actual_news_count}"
        )

        print(
            f"Stored news today     : {stored_news}"
        )

        print(
            f"Actual Jatim today    : {actual_jatim_count}"
        )

        print(
            f"Stored Jatim today    : {stored_jatim}"
        )

        print(
            f"Global case-high      : {actual_case_high_global}"
        )

        print(
            f"Jatim case-high       : {actual_case_high_jatim}"
        )

        print(
            "----------------------------------------"
        )

        for error in errors:

            print(
                "ERROR:",
                error
            )

        print(
            "========================================"
        )

        raise SystemExit(
            1
        )


    # ========================================================
    # SUCCESS
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
        "Tanggal monitoring menggunakan:"
    )

    print(
        "collected_at → published_at"
    )

    print(
        "----------------------------------------"
    )

    print(
        f"News records          : {len(news)}"
    )

    print(
        f"Case records          : {len(cases)}"
    )

    print(
        f"Case links            : {len(seen_article_case)}"
    )

    print(
        f"Today date            : {today}"
    )

    print(
        f"News today            : {actual_news_count}"
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
        f"Jatim today           : {actual_jatim_count}"
    )

    print(
        f"Jatim negative        : {actual_jatim_negative}"
    )

    print(
        f"Global case-high      : {actual_case_high_global}"
    )

    print(
        f"Jatim case-high       : {actual_case_high_jatim}"
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
