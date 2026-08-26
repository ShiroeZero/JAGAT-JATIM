import json
import os
import re
import hashlib
from datetime import datetime, timezone
from difflib import SequenceMatcher


NEWS_FILE = "data/news.json"
CASE_FILE = "data/cases.json"


def normalize(text):
    if not text:
        return ""

    text = text.lower()

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


def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


def make_case_id(title):

    normalized = normalize(title)

    return hashlib.sha1(
        normalized.encode("utf-8")
    ).hexdigest()[:16]


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

    if isinstance(data, list):
        return data

    return data.get(
        "items",
        []
    )


def load_cases():

    if not os.path.exists(
        CASE_FILE
    ):
        return []

    with open(
        CASE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if isinstance(data, list):
        return data

    return data.get(
        "cases",
        []
    )


def create_case(article):

    title = article.get(
        "title",
        ""
    )

    case_id = make_case_id(
        title
    )

    return {
        "id": case_id,

        "title": title,

        "region": article.get(
            "region"
        ),

        "is_jatim": article.get(
            "is_jatim",
            False
        ),

        "polres": article.get(
            "polres"
        ),

        "category": article.get(
            "category"
        ),

        "scope": article.get(
            "scope"
        ),

        "priority": article.get(
            "priority",
            "low"
        ),

        "articles": [
            {
                "title": title,
                "url": article.get(
                    "url"
                ),
                "source": article.get(
                    "source"
                ),
                "published_at": article.get(
                    "published_at"
                )
            }
        ],

        "media_count": 1,

        "first_seen": article.get(
            "published_at"
        ),

        "last_seen": article.get(
            "published_at"
        ),

        "status": "belum_ditindaklanjuti"
    }


def add_article_to_case(
    case,
    article
):

    case["articles"].append({

        "title": article.get(
            "title"
        ),

        "url": article.get(
            "url"
        ),

        "source": article.get(
            "source"
        ),

        "published_at": article.get(
            "published_at"
        )

    })


def process():

    news = load_news()

    cases = []

    # --------------------------------------------------
    # Hanya proses berita yang relevan
    # --------------------------------------------------

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


    # --------------------------------------------------
    # CLUSTERING
    # --------------------------------------------------

    for article in relevant_news:

        title = article.get(
            "title",
            ""
        )

        matched = None


        for case in cases:

            score = similarity(
                title,
                case["title"]
            )

            # Ambang awal.
            #
            # Nanti bisa kita tingkatkan
            # menggunakan entity extraction.

            if score >= 0.72:

                matched = case

                break


        if matched:

            add_article_to_case(
                matched,
                article
            )

            matched["media_count"] = len(
                set(
                    x.get(
                        "source"
                    )
                    for x in matched["articles"]
                    if x.get("source")
                )
            )

            published = article.get(
                "published_at"
            )

            if published:

                if not matched.get(
                    "first_seen"
                ) or published < matched["first_seen"]:

                    matched["first_seen"] = published


                if not matched.get(
                    "last_seen"
                ) or published > matched["last_seen"]:

                    matched["last_seen"] = published

        else:

            cases.append(
                create_case(
                    article
                )
            )


    # --------------------------------------------------
    # SORT
    # --------------------------------------------------

    cases.sort(

        key=lambda case:
            case.get(
                "last_seen",
                ""
            ),

        reverse=True
    )


    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    os.makedirs(
        "data",
        exist_ok=True
    )


    output = {

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

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
        "================================"
    )

    print(
        f"Articles : {len(news)}"
    )

    print(
        f"Cases    : {len(cases)}"
    )

    print(
        "================================"
    )


if __name__ == "__main__":

    process()
