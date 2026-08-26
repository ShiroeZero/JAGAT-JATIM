import json
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


OUT = "data/social.json"

API_URL = "https://www.googleapis.com/youtube/v3/search"

API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()


# ============================================================
# 39 SATKER / POLRES JAWA TIMUR
# ============================================================

POLRES_MAP = {
    "POLRES PELABUHAN TANJUNG PERAK": [
        "pelabuhan tanjung perak",
        "tanjung perak",
        "polres tanjung perak",
    ],

    "POLRES JEMBER": [
        "jember",
        "polres jember",
    ],

    "POLRES KEDIRI": [
        "polres kediri",
        "kabupaten kediri",
    ],

    "POLRES BLITAR KOTA": [
        "blitar kota",
        "polres blitar kota",
    ],

    "POLRESTABES SURABAYA": [
        "surabaya",
        "polrestabes surabaya",
    ],

    "POLRESTA MALANG KOTA": [
        "malang kota",
        "polresta malang kota",
    ],

    "POLRESTA SIDOARJO": [
        "sidoarjo",
        "polresta sidoarjo",
    ],

    "POLRESTA BANYUWANGI": [
        "banyuwangi",
        "polresta banyuwangi",
    ],

    "POLRESTA TUBAN": [
        "tuban",
        "polresta tuban",
    ],

    "POLRESTA SUMENEP": [
        "sumenep",
        "polresta sumenep",
    ],

    "POLRES GRESIK": [
        "gresik",
        "polres gresik",
    ],

    "POLRES MALANG": [
        "kabupaten malang",
        "polres malang",
    ],

    "POLRES PASURUAN": [
        "kabupaten pasuruan",
        "polres pasuruan",
    ],

    "POLRES PASURUAN KOTA": [
        "pasuruan kota",
        "polres pasuruan kota",
    ],

    "POLRES PROBOLINGGO": [
        "kabupaten probolinggo",
        "polres probolinggo",
    ],

    "POLRES PROBOLINGGO KOTA": [
        "probolinggo kota",
        "polres probolinggo kota",
    ],

    "POLRES LUMAJANG": [
        "lumajang",
        "polres lumajang",
    ],

    "POLRES BATU": [
        "kota batu",
        "batu malang",
        "polres batu",
    ],

    "POLRES BONDOWOSO": [
        "bondowoso",
        "polres bondowoso",
    ],

    "POLRES SITUBONDO": [
        "situbondo",
        "polres situbondo",
    ],

    "POLRES KEDIRI KOTA": [
        "kediri kota",
        "polres kediri kota",
    ],

    "POLRES TULUNGAGUNG": [
        "tulungagung",
        "polres tulungagung",
    ],

    "POLRES NGANJUK": [
        "nganjuk",
        "polres nganjuk",
    ],

    "POLRES TRENGGALEK": [
        "trenggalek",
        "polres trenggalek",
    ],

    "POLRES BLITAR": [
        "kabupaten blitar",
        "polres blitar",
    ],

    "POLRES MADIUN": [
        "kabupaten madiun",
        "polres madiun",
    ],

    "POLRES MADIUN KOTA": [
        "madiun kota",
        "polres madiun kota",
    ],

    "POLRES NGAWI": [
        "ngawi",
        "polres ngawi",
    ],

    "POLRES MAGETAN": [
        "magetan",
        "polres magetan",
    ],

    "POLRES PONOROGO": [
        "ponorogo",
        "polres ponorogo",
    ],

    "POLRES PACITAN": [
        "pacitan",
        "polres pacitan",
    ],

    "POLRES BOJONEGORO": [
        "bojonegoro",
        "polres bojonegoro",
    ],

    "POLRES LAMONGAN": [
        "lamongan",
        "polres lamongan",
    ],

    "POLRES MOJOKERTO": [
        "kabupaten mojokerto",
        "polres mojokerto",
    ],

    "POLRES MOJOKERTO KOTA": [
        "mojokerto kota",
        "polres mojokerto kota",
    ],

    "POLRES JOMBANG": [
        "jombang",
        "polres jombang",
    ],

    "POLRES PAMEKASAN": [
        "pamekasan",
        "polres pamekasan",
    ],

    "POLRES BANGKALAN": [
        "bangkalan",
        "polres bangkalan",
    ],

    "POLRES SAMPANG": [
        "sampang",
        "polres sampang",
    ],
}


# ============================================================
# JAWA TIMUR — HANYA BERDASARKAN KONTEN
# BUKAN NAMA CHANNEL
# ============================================================

JATIM_TERMS = [
    "jawa timur",
    "jawa-timur",
    "jatim",
    "surabaya",
    "sidoarjo",
    "gresik",
    "lamongan",
    "tuban",
    "bojonegoro",
    "ngawi",
    "magetan",
    "madiun",
    "ponorogo",
    "pacitan",
    "nganjuk",
    "kediri",
    "tulungagung",
    "blitar",
    "trenggalek",
    "malang",
    "batu",
    "pasuruan",
    "probolinggo",
    "lumajang",
    "jember",
    "bondowoso",
    "situbondo",
    "banyuwangi",
    "mojokerto",
    "jombang",
    "sampang",
    "pamekasan",
    "sumenep",
    "bangkalan",
    "madura",
    "polda jatim",
]


# ============================================================
# KATEGORI
# ============================================================

CATEGORIES = {

    "Oknum / Pelanggaran Anggota": [
        "oknum polisi",
        "oknum polri",
        "anggota polisi",
        "anggota polri",
        "polisi ditangkap",
        "polisi ditahan",
        "polisi tersangka",
        "polisi terlibat",
        "polisi diduga",
    ],

    "Etik / Disiplin": [
        "pelanggaran etik",
        "kode etik",
        "pelanggaran disiplin",
        "sidang etik",
        "propam",
        "disiplin polisi",
    ],

    "Narkoba": [
        "polisi narkoba",
        "polisi sabu",
        "polisi narkotika",
        "polisi ganja",
        "anggota polisi narkoba",
        "oknum polisi narkoba",
    ],

    "Korupsi / Suap / Pungli": [
        "polisi korupsi",
        "polisi suap",
        "polisi pungli",
        "polisi pemerasan",
        "polisi gratifikasi",
        "oknum polisi korupsi",
    ],

    "Kekerasan / Penganiayaan": [
        "polisi menganiaya",
        "polisi penganiayaan",
        "polisi kekerasan",
        "polisi menembak",
        "polisi penembakan",
        "oknum polisi menganiaya",
    ],

    "Penyalahgunaan Wewenang": [
        "penyalahgunaan wewenang polisi",
        "polisi salah gunakan wewenang",
        "oknum polisi memeras",
        "polisi memeras",
    ],

    "Kasus Hukum Lainnya": [
        "polisi tersangka",
        "polisi diperiksa",
        "polisi ditangkap",
        "polisi ditahan",
        "polisi terlibat kasus",
    ],
}


# ============================================================
# QUERY YOUTUBE
#
# Kita sengaja menggunakan sedikit query agar quota API tidak
# cepat habis. search.list adalah endpoint yang relatif mahal.
# ============================================================

SEARCH_QUERIES = [

    '"oknum polisi"',

    '"anggota polisi" tersangka',

    '"polisi" ditangkap',

    '"polisi" narkoba',

    '"polisi" korupsi',

    '"polisi" pelanggaran etik',

    '"polisi" penyalahgunaan wewenang',

    '"polisi" penganiayaan',

]


# ============================================================
# HELPERS
# ============================================================

def normalize(text):

    text = str(text or "").lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_term(text, term):

    text = normalize(text)
    term = normalize(term)

    return term in text


def detect_polres(text):

    text = normalize(text)

    # Urutkan nama terpanjang dahulu agar:
    # "kediri kota" tidak tertangkap sebagai "kediri"

    entries = sorted(
        POLRES_MAP.items(),
        key=lambda x: max(
            len(v)
            for v in x[1]
        ),
        reverse=True
    )

    for polres, aliases in entries:

        for alias in aliases:

            if contains_term(
                text,
                alias
            ):

                return polres

    return None


def detect_jatim(text):

    text = normalize(text)

    return any(
        term in text
        for term in JATIM_TERMS
    )


def detect_category(text):

    text = normalize(text)

    for category, terms in CATEGORIES.items():

        for term in terms:

            if term in text:

                return category

    return "Lainnya"


def detect_priority(
    title,
    description
):

    text = normalize(
        title + " " + description
    )

    high = [
        "ditangkap",
        "ditahan",
        "tersangka",
        "narkoba",
        "sabu",
        "korupsi",
        "suap",
        "pungli",
        "pemerasan",
        "penembakan",
        "penganiayaan",
        "tewas",
        "meninggal",
    ]

    medium = [
        "diduga",
        "diperiksa",
        "pelanggaran",
        "etik",
        "disiplin",
        "viral",
        "diselidiki",
    ]

    score = 0

    for word in high:

        if word in text:
            score += 2

    for word in medium:

        if word in text:
            score += 1

    if score >= 5:
        return "high"

    if score >= 2:
        return "medium"

    return "low"


def make_id(video_id):

    return hashlib.sha1(
        (
            "youtube|" +
            video_id
        ).encode("utf-8")
    ).hexdigest()


# ============================================================
# YOUTUBE REQUEST
# ============================================================

def youtube_search(
    query,
    published_after
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
        }

    )


    try:

        with urlopen(
            request,
            timeout=30
        ) as response:

            return json.loads(
                response.read()
            )


    except HTTPError as e:

        body = e.read().decode(
            "utf-8",
            errors="ignore"
        )

        print(
            f"YOUTUBE API ERROR "
            f"{e.code}: {body}"
        )

        return {}


    except URLError as e:

        print(
            f"YOUTUBE NETWORK ERROR: {e}"
        )

        return {}


# ============================================================
# LOAD OLD DATA
# ============================================================

def load_existing():

    if not os.path.exists(OUT):

        return []

    try:

        with open(
            OUT,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return data.get(
            "items",
            []
        )

    except Exception:

        return []


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
        "========================================"
    )


    if not API_KEY:

        raise RuntimeError(
            "YOUTUBE_API_KEY belum tersedia. "
            "Pastikan GitHub Secret bernama "
            "YOUTUBE_API_KEY."
        )


    # Ambil video sekitar 2 hari terakhir.
    #
    # Ini memberi overlap agar jika collector gagal satu jam,
    # video masih bisa ditemukan pada run berikutnya.

    now = datetime.now(
        timezone.utc
    )

    published_after = (
        now - timedelta(days=2)
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


    old_items = load_existing()


    # Deduplicate berdasarkan video ID

    items_by_video = {}

    for item in old_items:

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


    # ========================================================
    # SEARCH
    # ========================================================

    for index, query in enumerate(
        SEARCH_QUERIES,
        start=1
    ):

        print(
            f"[{index}/{len(SEARCH_QUERIES)}] "
            f"Searching: {query}"
        )


        response = youtube_search(
            query,
            published_after
        )


        results = response.get(
            "items",
            []
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

            snippet = result.get(
                "snippet",
                {}
            )


            if not video_id:
                continue


            title = (
                snippet.get(
                    "title"
                )
                or ""
            )


            description = (
                snippet.get(
                    "description"
                )
                or ""
            )


            channel = (
                snippet.get(
                    "channelTitle"
                )
                or ""
            )


            published_at = (
                snippet.get(
                    "publishedAt"
                )
                or ""
            )


            # =================================================
            # PENTING:
            # JANGAN menggunakan channel sebagai penentu Jatim.
            #
            # Penentuan wilayah hanya dari judul + deskripsi.
            # =================================================

            content = (
                title
                + " "
                + description
            )


            is_jatim = detect_jatim(
                content
            )


            polres = detect_polres(
                content
            )


            # Kalau Polres Jatim terdeteksi,
            # otomatis Jatim.

            if polres:

                is_jatim = True


            category = detect_category(
                content
            )


            priority = detect_priority(
                title,
                description
            )


            item = {

                "id":
                    make_id(video_id),

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
                    "https://www.youtube.com/watch?v="
                    + video_id,

                "thumbnail":
                    (
                        "https://i.ytimg.com/vi/"
                        + video_id
                        + "/hqdefault.jpg"
                    ),

                "description":
                    description[:1000],

                "region":
                    (
                        "Jawa Timur"
                        if is_jatim
                        else "Indonesia"
                    ),

                "is_jatim":
                    is_jatim,

                "polres":
                    polres,

                "category":
                    category,

                "priority":
                    priority,

                "collected_at":
                    now.isoformat(),
            }


            # Update jika video sudah pernah ditemukan

            if video_id in items_by_video:

                old = items_by_video[
                    video_id
                ]

                old.update(
                    item
                )

            else:

                items_by_video[
                    video_id
                ] = item

                added += 1


    # ========================================================
    # SORT + LIMIT
    # ========================================================

    items = list(
        items_by_video.values()
    )


    items.sort(

        key=lambda x:
            x.get(
                "published_at",
                ""
            ),

        reverse=True
    )


    # Simpan maksimal 1000 video

    items = items[:1000]


    output = {

        "generated_at":
            now.isoformat(),

        "platform":
            "YouTube",

        "total":
            len(items),

        "items":
            items,
    }


    os.makedirs(
        "data",
        exist_ok=True
    )


    with open(
        OUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )


    jatim_count = sum(
        1
        for x in items
        if x.get(
            "is_jatim"
        )
    )


    print(
        "========================================"
    )

    print(
        f"New videos     : {added}"
    )

    print(
        f"Total videos   : {len(items)}"
    )

    print(
        f"Jawa Timur     : {jatim_count}"
    )

    print(
        f"Output         : {OUT}"
    )

    print(
        "========================================"


    )


if __name__ == "__main__":

    main()
