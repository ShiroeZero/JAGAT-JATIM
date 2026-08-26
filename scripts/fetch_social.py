import json
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from classify_social import classify, detect_priority
from location_engine import detect_location


OUT = "data/social.json"

API_URL = (
    "https://www.googleapis.com/youtube/v3/search"
)

API_KEY = os.environ.get(
    "YOUTUBE_API_KEY",
    "",
).strip()


SEARCH_QUERIES = [
    '"oknum polisi"',
    '"anggota polisi" tersangka',
    '"polisi" ditangkap',
    '"polisi" narkoba',
    '"polisi" korupsi',
    '"polisi" suap',
    '"polisi" pungli',
    '"polisi" pelanggaran etik',
    '"polisi" penganiayaan',
    '"polisi" kekerasan',
    '"polisi" penyalahgunaan wewenang',
]


def youtube_search(
    query,
    published_after,
):

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "date",
        "maxResults": 25,
        "publishedAfter": published_after,
        "regionCode": "ID",
        "relevanceLanguage": "id",
        "key": API_KEY,
    }

    url = (
        API_URL
        + "?"
        + urlencode(params)
    )

    request = Request(
        url,
        headers={
            "User-Agent":
                "PNM-Social-Monitor/1.0",
        },
    )

    try:

        with urlopen(
            request,
            timeout=30,
        ) as response:

            return json.loads(
                response.read()
            )

    except HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="ignore",
        )

        raise RuntimeError(
            "YouTube API HTTP "
            + str(error.code)
            + ": "
            + body
        )

    except URLError as error:

        raise RuntimeError(
            "YouTube network error: "
            + str(error)
        )


def load_existing():

    if not os.path.exists(OUT):
        return []

    try:

        with open(
            OUT,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return data.get(
            "items",
            [],
        )

    except Exception:

        return []


def main():

    print(
        "========================================"
    )

    print(
        "PNM — YOUTUBE SOCIAL MONITOR V4"
    )

    print(
        "========================================"
    )

    if not API_KEY:

        raise RuntimeError(
            "YOUTUBE_API_KEY tidak tersedia."
        )

    now = datetime.now(
        timezone.utc
    )

    published_after = (
        now
        - timedelta(days=2)
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    existing = load_existing()

    items_by_video = {}

    for item in existing:

        video_id = item.get(
            "video_id"
        )

        if video_id:

            items_by_video[
                video_id
            ] = item

    print(
        f"Existing videos : "
        f"{len(items_by_video)}"
    )

    print(
        f"Searching since  : "
        f"{published_after}"
    )

    added = 0

    for index, query in enumerate(
        SEARCH_QUERIES,
        start=1,
    ):

        print(
            f"[{index}/{len(SEARCH_QUERIES)}] "
            f"Searching: {query}"
        )

        response = youtube_search(
            query,
            published_after,
        )

        results = response.get(
            "items",
            [],
        )

        print(
            f"    Results: "
            f"{len(results)}"
        )

        for result in results:

            video_id = (
                result
                .get("id", {})
                .get("videoId")
            )

            if not video_id:
                continue

            snippet = result.get(
                "snippet",
                {},
            )

            title = snippet.get(
                "title",
                "",
            )

            description = snippet.get(
                "description",
                "",
            )

            channel = snippet.get(
                "channelTitle",
                "",
            )

            published_at = snippet.get(
                "publishedAt",
                "",
            )

            classification = classify(
                title,
                description,
            )

            location = detect_location(
                title,
                description,
            )

            priority = detect_priority(
                classification,
                title,
                description,
            )

            item = {

                "video_id":
                    video_id,

                "platform":
                    "YouTube",

                "type":
                    "video",

                "title":
                    title,

                "channel":
                    channel,

                "published_at":
                    published_at,

                "url":
                    (
                        "https://www.youtube.com/watch?v="
                        + video_id
                    ),

                "thumbnail":
                    (
                        "https://i.ytimg.com/vi/"
                        + video_id
                        + "/hqdefault.jpg"
                    ),

                "description":
                    description[:1500],

                # ------------------------------------------
                # CLASSIFICATION
                # ------------------------------------------

                "scope":
                    classification[
                        "scope"
                    ],

                "category":
                    classification[
                        "category"
                    ],

                "role":
                    classification[
                        "role"
                    ],

                "classification_confidence":
                    classification[
                        "confidence"
                    ],

                "classification_reason":
                    classification[
                        "reason"
                    ],

                # ------------------------------------------
                # LOCATION
                # ------------------------------------------

                "is_jatim":
                    location[
                        "is_jatim"
                    ],

                "region":
                    location[
                        "region"
                    ],

                "polres":
                    location[
                        "polres"
                    ],

                "location_confidence":
                    location[
                        "confidence"
                    ],

                "location_source":
                    location[
                        "source"
                    ],

                "location_evidence":
                    location[
                        "evidence"
                    ],

                # ------------------------------------------
                # PRIORITY
                # ------------------------------------------

                "priority":
                    priority,

                "collected_at":
                    now.isoformat(),
            }

            if video_id in items_by_video:

                items_by_video[
                    video_id
                ].update(item)

            else:

                items_by_video[
                    video_id
                ] = item

                added += 1

    items = list(
        items_by_video.values()
    )

    items.sort(
        key=lambda item:
            item.get(
                "published_at",
                "",
            ),
        reverse=True,
    )

    items = items[:1500]

    stats = {

        "total":
            len(items),

        "new_videos":
            added,

        "jatim":
            sum(
                1
                for item in items
                if item.get(
                    "is_jatim"
                )
            ),

        "negative":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "negative"
            ),

        "incident":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "incident"
            ),

        "case":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "case"
            ),

        "neutral":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "neutral"
            ),

        "review":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "review"
            ),

        "noise":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "noise"
            ),

        "high_priority":
            sum(
                1
                for item in items
                if item.get(
                    "priority"
                ) == "high"
            ),
    }

    output = {

        "generated_at":
            now.isoformat(),

        "platform":
            "YouTube",

        "total":
            len(items),

        "new_videos":
            added,

        "statistics":
            stats,

        "items":
            items,
    }

    os.makedirs(
        "data",
        exist_ok=True,
    )

    with open(
        OUT,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "========================================"
    )

    print(
        f"New videos       : "
        f"{stats['new_videos']}"
    )

    print(
        f"Total videos     : "
        f"{stats['total']}"
    )

    print(
        f"Jawa Timur       : "
        f"{stats['jatim']}"
    )

    print(
        f"Negative Polri   : "
        f"{stats['negative']}"
    )

    print(
        f"Peristiwa        : "
        f"{stats['incident']}"
    )

    print(
        f"Ungkap kasus     : "
        f"{stats['case']}"
    )

    print(
        f"Netral           : "
        f"{stats['neutral']}"
    )

    print(
        f"Review           : "
        f"{stats['review']}"
    )

    print(
        f"Noise            : "
        f"{stats['noise']}"
    )

    print(
        f"Prioritas tinggi : "
        f"{stats['high_priority']}"
    )

    print(
        f"Output           : "
        f"{OUT}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
