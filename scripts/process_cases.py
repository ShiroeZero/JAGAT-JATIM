import json
import os
import re
import hashlib
from datetime import datetime, timezone
from difflib import SequenceMatcher


NEWS_FILE = "data/news.json"
CASE_FILE = "data/cases.json"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# IMPORTANT WORDS
# ============================================================

STOPWORDS = {
    "yang",
    "dan",
    "di",
    "ke",
    "dari",
    "untuk",
    "dengan",
    "dalam",
    "pada",
    "oleh",
    "karena",
    "agar",
    "atau",
    "ini",
    "itu",
    "akan",
    "telah",
    "sudah",
    "jadi",
    "ada",
    "tak",
    "tidak",
    "seorang",
    "sejumlah",
    "terkait",
    "soal",
    "kata",
    "ungkap",
    "ungkapnya",
    "berita",
    "kini",
    "hari",
    "polisi",
    "polri"
}


def keywords(text):

    words = normalize(text).split()

    return {
        word
        for word in words
        if len(word) >= 4
        and word not in STOPWORDS
    }


# ============================================================
# SIMILARITY
# ============================================================

def similarity(a, b):

    a_words = keywords(a)
    b_words = keywords(b)

    if not a_words or not b_words:
        return 0.0

    intersection = len(
        a_words & b_words
    )

    union = len(
        a_words | b_words
    )

    jaccard = (
        intersection / union
        if union
        else 0
    )

    sequence = SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()

    # Kombinasi keyword + urutan judul
    return (
        jaccard * 0.65
        +
        sequence * 0.35
    )


# ============================================================
# CASE ID
# ============================================================

def make_case_id(title):

    normalized = normalize(title)

    return hashlib.sha1(
        normalized.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# LOAD NEWS
# ============================================================

def load_news():

    if not os.path.exists(
        NEWS_FILE
    ):
        return []

    with open(
        NEWS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

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
# CREATE CASE
# ============================================================

def create_case(article):

    title = article.get(
        "title",
        ""
    )

    return {

        "id":
            make_case_id(title),

        "title":
            title,

        "region":
            article.get("region"),

        "is_jatim":
            article.get(
                "is_jatim",
                False
            ),

        "polres":
            article.get("polres"),

        "category":
            article.get("category"),

        "scope":
            article.get("scope"),

        "priority":
            article.get(
                "priority",
                "low"
            ),

        "articles": [

            {
                "title":
                    title,

                "url":
                    article.get("url"),

                "source":
                    article.get("source"),

                "published_at":
                    article.get(
                        "published_at"
                    )
            }

        ],

        "media_count":
            1,

        "first_seen":
            article.get(
                "published_at"
            ),

        "last_seen":
            article.get(
                "published_at"
            ),

        "status":
            "belum_ditindaklanjuti"
    }


# ============================================================
# ADD ARTICLE
# ============================================================

def add_article_to_case(
    case,
    article
):

    case["articles"].append({

        "title":
            article.get("title"),

        "url":
            article.get("url"),

        "source":
            article.get("source"),

        "published_at":
            article.get(
                "published_at"
            )
    })


# ============================================================
# CHECK SAME REGION
# ============================================================

def same_region(
    article,
    case
):

    article_region = (
        article.get("region")
        or ""
    ).lower().strip()

    case_region = (
        case.get("region")
        or ""
    ).lower().strip()

    if not article_region:
        return True

    if not case_region:
        return True

    return (
        article_region
        == case_region
    )


# ============================================================
# CHECK SAME POLRES
# ============================================================

def same_polres(
    article,
    case
):

    article_polres = (
        article.get("polres")
        or ""
    ).lower().strip()

    case_polres = (
        case.get("polres")
        or ""
    ).lower().strip()

    # Jika salah satu tidak diketahui,
    # jangan menjadikan ini penghalang.

    if not article_polres:
        return True

    if not case_polres:
        return True

    return (
        article_polres
        == case_polres
    )


# ============================================================
# BUILD INDEX
# ============================================================

def build_index(cases):

    index = {}

    for case_index, case in enumerate(
        cases
    ):

        title_words = keywords(
            case.get(
                "title",
                ""
            )
        )

        for word in title_words:

            index.setdefault(
                word,
                set()
            ).add(
                case_index
            )

    return index


# ============================================================
# FIND CANDIDATES
# ============================================================

def find_candidates(
    article,
    index
):

    article_words = keywords(
        article.get(
            "title",
            ""
        )
    )

    candidates = set()

    for word in article_words:

        if word in index:

            candidates.update(
                index[word]
            )

    return candidates


# ============================================================
# MAIN PROCESS
# ============================================================

def process():

    print(
        "========================================"
    )

    print(
        "PNM CASE CLUSTERING"
    )

    print(
        "========================================"
    )

    news = load_news()

    print(
        f"Total news loaded : {len(news)}"
    )


    relevant_news = [

        item

        for item in news

        if isinstance(
            item,
            dict
        )

        and item.get(
            "title"
        )
    ]


    print(
        f"News to process   : {len(relevant_news)}"
    )


    cases = []

    index = {}


    # ========================================================
    # PROCESS
    # ========================================================

    for counter, article in enumerate(
        relevant_news,
        start=1
    ):

        title = article.get(
            "title",
            ""
        )

        candidates = find_candidates(
            article,
            index
        )

        matched_case = None

        best_score = 0.0


        # ----------------------------------------------------
        # ONLY COMPARE WITH CANDIDATE CASES
        # ----------------------------------------------------

        for case_index in candidates:

            case = cases[
                case_index
            ]


            # Region guard
            if not same_region(
                article,
                case
            ):
                continue


            # Polres guard
            if not same_polres(
                article,
                case
            ):
                continue


            score = similarity(

                title,

                case.get(
                    "title",
                    ""
                )

            )


            if score > best_score:

                best_score = score

                matched_case = case


        # ----------------------------------------------------
        # MATCH
        # ----------------------------------------------------

        if (
            matched_case
            and best_score >= 0.55
        ):

            add_article_to_case(
                matched_case,
                article
            )


            matched_case[
                "media_count"
            ] = len(

                set(

                    x.get(
                        "source"
                    )

                    for x in matched_case[
                        "articles"
                    ]

                    if x.get(
                        "source"
                    )

                )

            )


            published = article.get(
                "published_at"
            )


            if published:

                first_seen = (
                    matched_case.get(
                        "first_seen"
                    )
                )

                last_seen = (
                    matched_case.get(
                        "last_seen"
                    )
                )


                if (
                    not first_seen
                    or published < first_seen
                ):

                    matched_case[
                        "first_seen"
                    ] = published


                if (
                    not last_seen
                    or published > last_seen
                ):

                    matched_case[
                        "last_seen"
                    ] = published


        # ----------------------------------------------------
        # NEW CASE
        # ----------------------------------------------------

        else:

            new_case = create_case(
                article
            )

            cases.append(
                new_case
            )

            new_index = (
                len(cases) - 1
            )


            # Add case to keyword index

            for word in keywords(
                title
            ):

                index.setdefault(
                    word,
                    set()
                ).add(
                    new_index
                )


        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        if (
            counter == 1
            or counter % 50 == 0
            or counter == len(
                relevant_news
            )
        ):

            print(
                f"Processed "
                f"{counter}/"
                f"{len(relevant_news)} "
                f"| Cases: "
                f"{len(cases)}"
            )


    # ========================================================
    # SORT
    # ========================================================

    cases.sort(

        key=lambda case:
            case.get(
                "last_seen",
                ""
            ),

        reverse=True
    )


    # ========================================================
    # OUTPUT
    # ========================================================

    os.makedirs(
        "data",
        exist_ok=True
    )


    output = {

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "total_cases":
            len(cases),

        "cases":
            cases

    }


    with open(
        CASE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            output,

            f,

            ensure_ascii=False,

            indent=2

        )


    print(
        "========================================"
    )

    print(
        f"Articles processed : "
        f"{len(relevant_news)}"
    )

    print(
        f"Cases generated    : "
        f"{len(cases)}"
    )

    print(
        f"Output             : "
        f"{CASE_FILE}"
    )

    print(
        "========================================"


    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    process()
