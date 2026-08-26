import json
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


OUT = "data/social.json"
API_URL = "https://www.googleapis.com/youtube/v3/search"

API_KEY = os.environ.get(
    "YOUTUBE_API_KEY",
    ""
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


# ============================================================
# TIME
# ============================================================

def now_utc():
    return datetime.now(timezone.utc)


def iso_z(dt):
    return dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


# ============================================================
# LOAD EXISTING DATABASE
# ============================================================

def load_database():

    if not os.path.exists(OUT):

        return {
            "generated_at": None,
            "platform": "YouTube",
            "total": 0,
            "new_videos": 0,
            "last_successful_fetch": None,
            "items": [],
        }

    try:

        with open(
            OUT,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "social.json bukan object JSON"
            )

        if not isinstance(
            data.get("items"),
            list,
        ):

            data["items"] = []

        return data

    except Exception as error:

        raise RuntimeError(
            "Gagal membaca "
            + OUT
            + ": "
            + str(error)
        )


# ============================================================
# BUILD INDEX
# ============================================================

def build_video_index(items):

    index = {}

    for item in items:

        video_id = item.get(
            "video_id"
        )

        if not video_id:
            continue

        index[video_id] = item

    return index


# ============================================================
# YOUTUBE API
# ============================================================

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

        "publishedAfter":
            published_after,

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
                "PNM-Social-Monitor/1.0"
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


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "PNM — YOUTUBE SOCIAL MONITOR"
    )

    print(
        "INCREMENTAL FETCH V1"
    )

    print(
        "========================================"
    )

    if not API_KEY:

        raise RuntimeError(
            "YOUTUBE_API_KEY tidak tersedia."
        )

    now = now_utc()

    database = load_database()

    existing_items = database.get(
        "items",
        [],
    )

    video_index = build_video_index(
        existing_items
    )

    existing_count = len(
        video_index
    )

    # ========================================================
    # LAST SUCCESSFUL FETCH
    # ========================================================

    last_successful_fetch = database.get(
        "last_successful_fetch"
    )

    if last_successful_fetch:

        published_after = (
            last_successful_fetch
        )

        fetch_mode = "INCREMENTAL"

    else:

        # ----------------------------------------------------
        # FIRST RUN / MIGRATION
        #
        # Kalau timestamp belum ada, ambil 2 hari terakhir.
        # Data lama tetap dipertahankan dan didedup.
        # ----------------------------------------------------

        published_after = iso_z(
            now - timedelta(days=2)
        )

        fetch_mode = "INITIAL"

    print(
        f"Existing videos : {existing_count}"
    )

    print(
        f"Fetch mode      : {fetch_mode}"
    )

    print(
        f"Searching since : {published_after}"
    )

    # ========================================================
    # FETCH
    # ========================================================

    new_items = {}

    total_api_results = 0

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

        total_api_results += len(
            results
        )

        print(
            f"    Results: {len(results)}"
        )

        for result in results:

            video_id = (
                result
                .get("id", {})
                .get("videoId")
            )

            if not video_id:
                continue

            # ------------------------------------------------
            # EXISTING VIDEO
            # ------------------------------------------------

            if video_id in video_index:

                continue

            # ------------------------------------------------
            # DUPLICATE WITHIN CURRENT RUN
            # ------------------------------------------------

            if video_id in new_items:

                continue

            snippet = result.get(
                "snippet",
                {},
            )

            item = {

                "video_id":
                    video_id,

                "platform":
                    "YouTube",

                "type":
                    "video",

                "title":
                    snippet.get(
                        "title",
                        "",
                    ),

                "channel":
                    snippet.get(
                        "channelTitle",
                        "",
                    ),

                "published_at":
                    snippet.get(
                        "publishedAt",
                        "",
                    ),

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
                    snippet.get(
                        "description",
                        "",
                    )[:1500],

                # ------------------------------------------------
                # CLASSIFICATION AKAN DIISI TAHAP BERIKUTNYA
                # ------------------------------------------------

                "scope": None,

                "category": None,

                "role": None,

                "classification_confidence":
                    None,

                "classification_reason":
                    [],

                # ------------------------------------------------
                # LOCATION AKAN DIISI TAHAP BERIKUTNYA
                # ------------------------------------------------

                "is_jatim":
                    None,

                "region":
                    None,

                "polres":
                    None,

                "location_confidence":
                    None,

                "location_source":
                    None,

                "location_evidence":
                    [],

                # ------------------------------------------------
                # PRIORITY AKAN DIISI TAHAP BERIKUTNYA
                # ------------------------------------------------

                "priority":
                    None,

                # ------------------------------------------------
                # PROCESSING STATE
                # ------------------------------------------------

                "processing_status":
                    "new",

                "classifier_version":
                    None,

                "classified_at":
                    None,

                "case_id":
                    None,

                "collected_at":
                    now.isoformat(),
            }

            new_items[
                video_id
            ] = item

    # ========================================================
    # APPEND ONLY NEW ITEMS
    # ========================================================

    for video_id, item in new_items.items():

        video_index[
            video_id
        ] = item

    all_items = list(
        video_index.values()
    )

    # ========================================================
    # SORT
    # ========================================================

    all_items.sort(
        key=lambda item:
            item.get(
                "published_at",
                "",
            ),
        reverse=True,
    )

    # ========================================================
    # SAVE
    #
    # PENTING:
    # last_successful_fetch BARU
    # ditulis setelah SEMUA API CALL sukses.
    # ========================================================

    database = {

        "generated_at":
            now.isoformat(),

        "platform":
            "YouTube",

        "total":
            len(all_items),

        "new_videos":
            len(new_items),

        "last_successful_fetch":
            iso_z(now),

        "last_fetch_mode":
            fetch_mode,

        "last_api_results":
            total_api_results,

        "items":
            all_items,
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
            database,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # LOG
    # ========================================================

    print(
        "========================================"
    )

    print(
        f"API results      : "
        f"{total_api_results}"
    )

    print(
        f"New videos       : "
        f"{len(new_items)}"
    )

    print(
        f"Existing videos  : "
        f"{existing_count}"
    )

    print(
        f"Total videos     : "
        f"{len(all_items)}"
    )

    print(
        f"Fetch mode       : "
        f"{fetch_mode}"
    )

    print(
        f"Last successful  : "
        f"{iso_z(now)}"
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
