import json
import os
import re
import hashlib
from datetime import datetime, timezone
from difflib import SequenceMatcher


NEWS_FILE = "data/news.json"
CASE_FILE = "data/case_clusters.json"

ENGINE_VERSION = "case-v2"

# ------------------------------------------------------------
# MATCHING THRESHOLDS
# ------------------------------------------------------------

TITLE_MATCH_THRESHOLD = 0.72
WORD_MATCH_THRESHOLD = 0.58

MAX_CASES_TO_COMPARE = 250


# ============================================================
# TIME
# ============================================================

def now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# TEXT NORMALIZATION
# ============================================================

STOPWORDS = {
    "yang",
    "dan",
    "di",
    "ke",
    "dari",
    "untuk",
    "dengan",
    "pada",
    "dalam",
    "oleh",
    "ini",
    "itu",
    "seorang",
    "orang",
    "jadi",
    "akan",
    "telah",
    "adalah",
    "terkait",
    "soal",
    "kasus",
    "berita",
    "polisi",
    "polri",
}


def normalize(text):

    text = (
        text or ""
    ).lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def words(text):

    normalized = normalize(
        text
    )

    return {
        word
        for word in normalized.split()
        if (
            len(word) >= 3
            and word not in STOPWORDS
        )
    }


def similarity(a, b):

    a_words = words(a)
    b_words = words(b)

    if not a_words or not b_words:
        return 0.0

    intersection = (
        a_words
        & b_words
    )

    union = (
        a_words
        | b_words
    )

    jaccard = (
        len(intersection)
        / len(union)
    )

    sequence = SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()

    return (
        jaccard * 0.65
        + sequence * 0.35
    )


# ============================================================
# DATABASE
# ============================================================

def load_json(path, default):

    if not os.path.exists(path):

        return default

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


def save_json(path, data):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    temp = (
        path
        + ".tmp"
    )

    with open(
        temp,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temp,
        path
    )


# ============================================================
# NEWS
# ============================================================

def load_news():

    data = load_json(
        NEWS_FILE,
        {
            "items": []
        }
    )

    if isinstance(
        data,
        list
    ):

        return data

    return data.get(
        "items",
        []
    )


# ============================================================
# CASE DATABASE
# ============================================================

def load_cases():

    data = load_json(
        CASE_FILE,
        None
    )

    if data is None:

        return {
            "engine_version":
                ENGINE_VERSION,

            "generated_at":
                now_iso(),

            "total_cases":
                0,

            "cases":
                []
        }

    # --------------------------------------------------------
    # Support beberapa kemungkinan format lama
    # --------------------------------------------------------

    if isinstance(
        data,
        list
    ):

        return {
            "engine_version":
                ENGINE_VERSION,

            "generated_at":
                now_iso(),

            "total_cases":
                len(data),

            "cases":
                data
        }

    if "cases" not in data:

        data["cases"] = []

    return data


# ============================================================
# CASE ID
# ============================================================

def next_case_id(cases):

    highest = 0

    for case in cases:

        value = str(
            case.get(
                "case_id",
                ""
            )
        )

        match = re.search(
            r"(\d+)$",
            value
        )

        if match:

            highest = max(
                highest,
                int(
                    match.group(1)
                )
            )

    return (
        f"CASE-{highest + 1:06d}"
    )


# ============================================================
# CASE TITLE
# ============================================================

def make_case_title(news):

    title = (
        news.get(
            "title"
        )
        or "Kasus tidak teridentifikasi"
    )

    return title[:180]


# ============================================================
# CASE SIGNATURE
# ============================================================

def case_signature(news):

    parts = [

        news.get(
            "polres"
        ),

        news.get(
            "category"
        ),

        news.get(
            "scope"
        ),

        news.get(
            "region"
        ),
    ]

    return " ".join(
        str(x)
        for x in parts
        if x
    )


# ============================================================
# ELIGIBILITY
# ============================================================

def is_case_candidate(news):

    scope = (
        news.get(
            "scope"
        )
        or ""
    ).lower()

    category = (
        news.get(
            "category"
        )
        or ""
    ).lower()

    # --------------------------------------------------------
    # Case engine tidak perlu meng-cluster semua berita netral.
    # --------------------------------------------------------

    if scope == "case":
        return True

    if scope == "negative":
        return True

    negative_words = [
        "oknum",
        "etik",
        "disiplin",
        "penyalahgunaan",
        "pungli",
        "suap",
        "pemerasan",
        "penganiayaan",
        "narkoba",
        "korupsi",
        "kekerasan",
    ]

    return any(
        word in category
        for word in negative_words
    )


# ============================================================
# CASE MATCH
# ============================================================

def find_matching_case(
    news,
    cases
):

    title = news.get(
        "title",
        ""
    )

    signature = case_signature(
        news
    )

    candidates = []

    # --------------------------------------------------------
    # CASE TERBARU LEBIH RELEVAN
    # --------------------------------------------------------

    sorted_cases = sorted(
        cases,
        key=lambda case:
            case.get(
                "last_seen",
                ""
            ),
        reverse=True
    )

    for case in sorted_cases[
        :MAX_CASES_TO_COMPARE
    ]:

        # ----------------------------------------------------
        # Polres conflict
        # ----------------------------------------------------

        news_polres = (
            news.get(
                "polres"
            )
        )

        case_polres = (
            case.get(
                "polres"
            )
        )

        if (
            news_polres
            and case_polres
            and news_polres != case_polres
        ):

            continue

        # ----------------------------------------------------
        # Category conflict
        # ----------------------------------------------------

        news_category = (
            news.get(
                "category"
            )
        )

        case_category = (
            case.get(
                "category"
            )
        )

        if (
            news_category
            and case_category
            and news_category != case_category
        ):

            # Negative / case masih bisa berhubungan.
            # Jangan langsung reject.
            pass

        # ----------------------------------------------------
        # Compare case title
        # ----------------------------------------------------

        case_title = case.get(
            "title",
            ""
        )

        score_title = similarity(
            title,
            case_title
        )

        # ----------------------------------------------------
        # Compare signature
        # ----------------------------------------------------

        score_signature = similarity(
            signature,
            case.get(
                "signature",
                ""
            )
        )

        score = (
            score_title * 0.75
            + score_signature * 0.25
        )

        candidates.append(
            (
                score,
                case
            )
        )

    if not candidates:

        return None, 0.0

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_score, best_case = (
        candidates[0]
    )

    if (
        best_score
        >= TITLE_MATCH_THRESHOLD
    ):

        return (
            best_case,
            best_score
        )

    return (
        None,
        best_score
    )


# ============================================================
# ADD ARTICLE TO CASE
# ============================================================

def attach_news(
    case,
    news,
    score
):

    news_id = news.get(
        "id"
    )

    if not news_id:

        return

    if (
        "article_ids"
        not in case
    ):

        case[
            "article_ids"
        ] = []

    if (
        news_id
        not in case[
            "article_ids"
        ]
    ):

        case[
            "article_ids"
        ].append(
            news_id
        )

    if (
        "articles"
        not in case
    ):

        case[
            "articles"
        ] = []

    # --------------------------------------------------------
    # Store compact article reference.
    # Jangan duplikasi seluruh berita ke case_clusters.json.
    # --------------------------------------------------------

    existing_ids = {
        article.get(
            "id"
        )
        for article in case[
            "articles"
        ]
    }

    if news_id not in existing_ids:

        case[
            "articles"
        ].append(
            {
                "id":
                    news_id,

                "title":
                    news.get(
                        "title",
                        ""
                    ),

                "url":
                    news.get(
                        "url",
                        ""
                    ),

                "published_at":
                    news.get(
                        "published_at"
                    ),

                "source":
                    news.get(
                        "source"
                    ),

                "match_score":
                    round(
                        score,
                        4
                    ),
            }
        )

    case[
        "article_count"
    ] = len(
        case[
            "article_ids"
        ]
    )

    case[
        "last_seen"
    ] = max(
        case.get(
            "last_seen",
            ""
        ),
        news.get(
            "published_at",
            ""
        )
    )


# ============================================================
# CREATE CASE
# ============================================================

def create_case(
    news,
    cases
):

    case_id = next_case_id(
        cases
    )

    published_at = (
        news.get(
            "published_at"
        )
        or now_iso()
    )

    signature = case_signature(
        news
    )

    case = {

        "case_id":
            case_id,

        "title":
            make_case_title(
                news
            ),

        "category":
            news.get(
                "category"
            ),

        "scope":
            news.get(
                "scope"
            ),

        "region":
            news.get(
                "region"
            ),

        "is_jatim":
            news.get(
                "is_jatim"
            ),

        "polres":
            news.get(
                "polres"
            ),

        "priority":
            news.get(
                "priority"
            ),

        "signature":
            signature,

        "first_seen":
            published_at,

        "last_seen":
            published_at,

        "article_ids":
            [],

        "articles":
            [],

        "article_count":
            0,

        "created_at":
            now_iso(),

        "updated_at":
            now_iso(),

        "engine_version":
            ENGINE_VERSION,
    }

    attach_news(
        case,
        news,
        1.0
    )

    cases.append(
        case
    )

    return case


# ============================================================
# UPDATE NEWS STATE
# ============================================================

def mark_processed(
    news,
    case_id
):

    news[
        "processing_status"
    ] = "processed"

    news[
        "case_id"
    ] = case_id

    news[
        "case_processed_at"
    ] = now_iso()

    news[
        "case_engine_version"
    ] = ENGINE_VERSION


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "PNM CASE CLUSTERING V2"
    )

    print(
        "INCREMENTAL CASE ENGINE"
    )

    print(
        "========================================"
    )

    news = load_news()

    database = load_cases()

    cases = database.get(
        "cases",
        []
    )

    print(
        f"Total news loaded : {len(news)}"
    )

    print(
        f"Existing cases    : {len(cases)}"
    )

    # ========================================================
    # FIND ONLY UNPROCESSED
    # ========================================================

    pending = []

    already_processed = 0

    for item in news:

        status = item.get(
            "processing_status"
        )

        case_id = item.get(
            "case_id"
        )

        # ----------------------------------------------------
        # Kalau sudah punya case_id + processed → SKIP
        # ----------------------------------------------------

        if (
            status == "processed"
            and case_id
        ):

            already_processed += 1

            continue

        # ----------------------------------------------------
        # Kalau tidak layak menjadi case:
        # tetap tandai processed supaya tidak diperiksa lagi.
        # ----------------------------------------------------

        if not is_case_candidate(
            item
        ):

            item[
                "processing_status"
            ] = "processed"

            item[
                "case_id"
            ] = None

            item[
                "case_processed_at"
            ] = now_iso()

            item[
                "case_engine_version"
            ] = ENGINE_VERSION

            already_processed += 1

            continue

        pending.append(
            item
        )

    print(
        f"Already processed : "
        f"{already_processed}"
    )

    print(
        f"News to process   : "
        f"{len(pending)}"
    )

    print(
        "========================================"
    )

    # ========================================================
    # PROCESS ONLY PENDING
    # ========================================================

    matched = 0
    created = 0

    for index, item in enumerate(
        pending,
        start=1
    ):

        title = item.get(
            "title",
            ""
        )

        print(
            f"Processed "
            f"{index}/{len(pending)}"
            f" | Cases: {len(cases)}"
            f" | {title[:90]}"
        )

        existing_case, score = (
            find_matching_case(
                item,
                cases
            )
        )

        if existing_case:

            attach_news(
                existing_case,
                item,
                score
            )

            existing_case[
                "updated_at"
            ] = now_iso()

            # ------------------------------------------------
            # Priority case bisa naik, tidak turun.
            # ------------------------------------------------

            priority_order = {
                "low": 1,
                "medium": 2,
                "high": 3,
            }

            old_priority = (
                existing_case.get(
                    "priority",
                    "low"
                )
            )

            new_priority = (
                item.get(
                    "priority",
                    "low"
                )
            )

            if (
                priority_order.get(
                    new_priority,
                    1
                )
                >
                priority_order.get(
                    old_priority,
                    1
                )
            ):

                existing_case[
                    "priority"
                ] = new_priority

            mark_processed(
                item,
                existing_case[
                    "case_id"
                ]
            )

            matched += 1

        else:

            new_case = create_case(
                item,
                cases
            )

            mark_processed(
                item,
                new_case[
                    "case_id"
                ]
            )

            created += 1

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    database = {

        "engine_version":
            ENGINE_VERSION,

        "generated_at":
            now_iso(),

        "total_cases":
            len(cases),

        "total_articles":
            sum(
                case.get(
                    "article_count",
                    0
                )
                for case in cases
            ),

        "last_run": {

            "news_loaded":
                len(news),

            "already_processed":
                already_processed,

            "pending":
                len(pending),

            "matched_existing":
                matched,

            "new_cases":
                created,
        },

        "cases":
            cases,
    }

    save_json(
        CASE_FILE,
        database
    )

    # ========================================================
    # SAVE NEWS
    # ========================================================

    news_database = load_json(
        NEWS_FILE,
        {}
    )

    if isinstance(
        news_database,
        dict
    ):

        news_database[
            "items"
        ] = news

        news_database[
            "case_engine_version"
        ] = ENGINE_VERSION

        news_database[
            "case_engine_processed_at"
        ] = now_iso()

        save_json(
            NEWS_FILE,
            news_database
        )

    # ========================================================
    # FINAL LOG
    # ========================================================

    print(
        "========================================"
    )

    print(
        "CASE ENGINE COMPLETE"
    )

    print(
        f"Total news       : {len(news)}"
    )

    print(
        f"Already processed: "
        f"{already_processed}"
    )

    print(
        f"Processed now    : "
        f"{len(pending)}"
    )

    print(
        f"Matched existing : "
        f"{matched}"
    )

    print(
        f"New cases        : "
        f"{created}"
    )

    print(
        f"Total cases      : "
        f"{len(cases)}"
    )

    total_articles = sum(
        case.get("article_count", 0)
        for case in cases
    )
    
    print(
        f"Total articles   : {total_articles}"
    )

    print(
        f"Output           : "
        f"{CASE_FILE}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":

    main()
