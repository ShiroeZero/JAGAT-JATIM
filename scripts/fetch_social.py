import json
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# PNM — SOCIAL MONITOR
# YouTube Data API v3
# ============================================================

OUT = "data/social.json"
API_URL = "https://www.googleapis.com/youtube/v3/search"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()


# ============================================================
# 39 POLRES / SATWIL JAWA TIMUR
# ============================================================

POLRES_MAP = {
    "POLRES PELABUHAN TANJUNG PERAK": [
        "polres pelabuhan tanjung perak",
        "pelabuhan tanjung perak",
        "tanjung perak",
    ],

    "POLRES JEMBER": [
        "polres jember",
        "kabupaten jember",
        "jember",
    ],

    "POLRES KEDIRI": [
        "polres kediri",
        "kabupaten kediri",
    ],

    "POLRES BLITAR KOTA": [
        "polres blitar kota",
        "blitar kota",
    ],

    "POLRESTABES SURABAYA": [
        "polrestabes surabaya",
        "surabaya",
    ],

    "POLRESTA MALANG KOTA": [
        "polresta malang kota",
        "malang kota",
    ],

    "POLRESTA SIDOARJO": [
        "polresta sidoarjo",
        "sidoarjo",
    ],

    "POLRESTA BANYUWANGI": [
        "polresta banyuwangi",
        "banyuwangi",
    ],

    "POLRESTA TUBAN": [
        "polresta tuban",
        "tuban",
    ],

    "POLRESTA SUMENEP": [
        "polresta sumenep",
        "sumenep",
    ],

    "POLRES GRESIK": [
        "polres gresik",
        "gresik",
    ],

    "POLRES MALANG": [
        "polres malang",
        "kabupaten malang",
    ],

    "POLRES PASURUAN": [
        "polres pasuruan",
        "kabupaten pasuruan",
    ],

    "POLRES PASURUAN KOTA": [
        "polres pasuruan kota",
        "pasuruan kota",
    ],

    "POLRES PROBOLINGGO": [
        "polres probolinggo",
        "kabupaten probolinggo",
    ],

    "POLRES PROBOLINGGO KOTA": [
        "polres probolinggo kota",
        "probolinggo kota",
    ],

    "POLRES LUMAJANG": [
        "polres lumajang",
        "lumajang",
    ],

    "POLRES BATU": [
        "polres batu",
        "kota batu",
    ],

    "POLRES BONDOWOSO": [
        "polres bondowoso",
        "bondowoso",
    ],

    "POLRES SITUBONDO": [
        "polres situbondo",
        "situbondo",
    ],

    "POLRES KEDIRI KOTA": [
        "polres kediri kota",
        "kediri kota",
    ],

    "POLRES TULUNGAGUNG": [
        "polres tulungagung",
        "tulungagung",
    ],

    "POLRES NGANJUK": [
        "polres nganjuk",
        "nganjuk",
    ],

    "POLRES TRENGGALEK": [
        "polres trenggalek",
        "trenggalek",
    ],

    "POLRES BLITAR": [
        "polres blitar",
        "kabupaten blitar",
    ],

    "POLRES MADIUN": [
        "polres madiun",
        "kabupaten madiun",
    ],

    "POLRES MADIUN KOTA": [
        "polres madiun kota",
        "madiun kota",
    ],

    "POLRES NGAWI": [
        "polres ngawi",
        "ngawi",
    ],

    "POLRES MAGETAN": [
        "polres magetan",
        "magetan",
    ],

    "POLRES PONOROGO": [
        "polres ponorogo",
        "ponorogo",
    ],

    "POLRES PACITAN": [
        "polres pacitan",
        "pacitan",
    ],

    "POLRES BOJONEGORO": [
        "polres bojonegoro",
        "bojonegoro",
    ],

    "POLRES LAMONGAN": [
        "polres lamongan",
        "lamongan",
    ],

    "POLRES MOJOKERTO": [
        "polres mojokerto",
        "kabupaten mojokerto",
    ],

    "POLRES MOJOKERTO KOTA": [
        "polres mojokerto kota",
        "mojokerto kota",
    ],

    "POLRES JOMBANG": [
        "polres jombang",
        "jombang",
    ],

    "POLRES PAMEKASAN": [
        "polres pamekasan",
        "pamekasan",
    ],

    "POLRES BANGKALAN": [
        "polres bangkalan",
        "bangkalan",
    ],

    "POLRES SAMPANG": [
        "polres sampang",
        "sampang",
    ],
}


# ============================================================
# KOTA / KABUPATEN JAWA TIMUR
# ============================================================

JATIM_LOCATIONS = [
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
    "pamekasan",
    "bangkalan",
    "sampang",
    "sumenep",
    "madura",
]


# ============================================================
# LUAR JAWA TIMUR
# Negative evidence.
# ============================================================

OUTSIDE_LOCATIONS = [
    "riau",
    "pekanbaru",
    "lampung",
    "lampung utara",
    "bandar lampung",
    "sumatera selatan",
    "palembang",
    "baturaja",
    "oku",
    "oku timur",
    "jakarta",
    "jakarta barat",
    "jakarta timur",
    "jakarta selatan",
    "jakarta utara",
    "tangerang",
    "tangerang selatan",
    "banten",
    "bandung",
    "jawa barat",
    "jawa tengah",
    "semarang",
    "yogyakarta",
    "daerah istimewa yogyakarta",
    "bali",
    "denpasar",
    "pontianak",
    "kalimantan",
    "sulawesi",
    "morowali",
    "padang",
    "sumatera barat",
    "batam",
    "kepulauan riau",
]


# ============================================================
# QUERY YOUTUBE
# ============================================================

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
# BASIC TERMS
# ============================================================

POLRI_TERMS = [
    "polisi",
    "polri",
    "oknum polisi",
    "oknum polri",
    "anggota polisi",
    "anggota polri",
    "polda",
    "polres",
    "polresta",
    "polrestabes",
    "propam",
    "kapolres",
    "kapolda",
]


NEGATIVE_TERMS = [
    "oknum",
    "pelanggaran etik",
    "pelanggaran disiplin",
    "penyalahgunaan wewenang",
    "korupsi",
    "suap",
    "pungli",
    "pemerasan",
    "narkoba",
    "narkotika",
    "sabu",
    "penganiayaan",
    "kekerasan",
    "penembakan",
    "ditangkap",
    "ditahan",
    "tersangka",
    "terlibat",
    "diduga",
]


NOISE_TERMS = [
    "game",
    "remix",
    "dubbing",
    "mainan",
    "meme",
    "parodi",
    "komedi",
    "challenge",
]


CASE_ACTION_TERMS = [
    "polisi menangkap",
    "polisi ungkap",
    "polisi mengungkap",
    "polisi amankan",
    "polisi mengamankan",
    "polisi berhasil menangkap",
    "polisi berhasil mengungkap",
    "ditangkap polisi",
    "diamankan polisi",
    "diamankan oleh polisi",
    "ditangkap oleh polisi",
]


# ============================================================
# POLISI SEBAGAI KORBAN
# ============================================================

POLICE_VICTIM_PATTERNS = [
    r"(polisi|anggota polisi|anggota polri).{0,100}"
    r"(ditembak|tertembak|ditabrak|dianiaya|diserang|terluka|tewas|meninggal)",

    r"(polisi|anggota polisi|anggota polri).{0,100}"
    r"(menjadi korban|jadi korban)",

    r"(3|dua|dua orang|beberapa).{0,30}"
    r"(polisi|anggota polisi|anggota polri).{0,80}"
    r"(terluka|tewas|meninggal|ditembak)",
]


# ============================================================
# POLISI SEBAGAI PELAKU
# ============================================================

POLICE_NEGATIVE_PATTERNS = [
    r"oknum\s+(polisi|polri)",

    r"(anggota\s+)?(polisi|polri).{0,100}"
    r"(ditangkap|ditahan|tersangka|terlibat|diduga)",

    r"(polisi|polri).{0,100}"
    r"(korupsi|suap|pungli|pemerasan)",

    r"(polisi|polri).{0,100}"
    r"(narkoba|narkotika|sabu|ganja)",

    r"(polisi|polri).{0,100}"
    r"(penganiayaan|kekerasan|penembakan)",

    r"(polisi|polri).{0,100}"
    r"(pelanggaran\s+etik|pelanggaran\s+disiplin)",

    r"(polisi|polri).{0,100}"
    r"penyalahgunaan\s+wewenang",
]


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    text = str(text or "").lower()

    text = re.sub(
        r"&amp;",
        " dan ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_word(text, term):
    """
    Word-boundary matching.

    Mencegah:
        batu -> baturaja
        madiun -> madiun? tetap cocok
    """

    text = normalize(text)
    term = normalize(term)

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(term)
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        text
    ) is not None


def make_id(video_id):

    return hashlib.sha1(
        (
            "youtube|"
            + video_id
        ).encode("utf-8")
    ).hexdigest()


# ============================================================
# DETECT POLRES
# ============================================================

def detect_polres(text):

    candidates = []

    for polres, aliases in POLRES_MAP.items():

        for alias in aliases:

            if contains_word(
                text,
                alias
            ):

                candidates.append(
                    (
                        len(alias),
                        polres,
                        alias
                    )
                )

    if not candidates:
        return None, None

    # Alias terpanjang menang.
    candidates.sort(
        reverse=True
    )

    _, polres, evidence = candidates[0]

    return polres, evidence


# ============================================================
# DETECT JATIM LOCATION
# ============================================================

def detect_jatim_locations(text):

    found = []

    for location in JATIM_LOCATIONS:

        if contains_word(
            text,
            location
        ):

            found.append(
                location
            )

    return found


# ============================================================
# DETECT OUTSIDE LOCATION
# ============================================================

def detect_outside_locations(text):

    found = []

    for location in OUTSIDE_LOCATIONS:

        if contains_word(
            text,
            location
        ):

            found.append(
                location
            )

    return found


# ============================================================
# LOCATION SCORING
# ============================================================

def detect_location(
    title,
    description
):

    title_n = normalize(title)
    description_n = normalize(description)

    combined = (
        title_n
        + " "
        + description_n
    )

    score = 0
    evidence = []
    source = None
    polres = None

    # --------------------------------------------------------
    # 1. POLRES
    # Strongest evidence.
    # --------------------------------------------------------

    detected_polres, polres_evidence = detect_polres(
        combined
    )

    if detected_polres:

        polres = detected_polres

        score += 100

        evidence.append(
            polres_evidence
        )

        source = "polres"

    # --------------------------------------------------------
    # 2. JAWA TIMUR EXPLICIT
    # --------------------------------------------------------

    if (
        contains_word(
            combined,
            "jawa timur"
        )
        or
        contains_word(
            combined,
            "jatim"
        )
    ):

        score += 80

        evidence.append(
            "Jawa Timur/Jatim"
        )

        if source is None:
            source = "province"

    # --------------------------------------------------------
    # 3. KOTA/KABUPATEN
    # --------------------------------------------------------

    jatim_locations = detect_jatim_locations(
        combined
    )

    for location in jatim_locations:

        if contains_word(
            title_n,
            location
        ):

            score += 60

        else:

            score += 35

        evidence.append(
            location
        )

        if source is None:
            source = "location"

    # --------------------------------------------------------
    # 4. LUAR JATIM
    # --------------------------------------------------------

    outside_locations = detect_outside_locations(
        combined
    )

    if outside_locations and not polres:

        score -= 100

        for location in outside_locations:

            evidence.append(
                "LUAR:" + location
            )

        if source is None:
            source = "outside"

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    is_jatim = score >= 35

    # Bukti luar Jatim kuat mengalahkan
    # keyword kota yang lemah.

    if (
        outside_locations
        and not polres
        and score < 80
    ):

        is_jatim = False

    confidence = min(
        100,
        max(
            0,
            score
        )
    )

    return {
        "is_jatim": is_jatim,
        "polres": polres,
        "confidence": confidence,
        "source": source,
        "evidence": evidence,
    }


# ============================================================
# CONTENT CLASSIFICATION
# ============================================================

def classify_content(
    title,
    description
):

    title_n = normalize(title)
    description_n = normalize(description)

    text = (
        title_n
        + " "
        + description_n
    )

    # --------------------------------------------------------
    # POLRI RELEVANCE
    # --------------------------------------------------------

    polri_hits = []

    for term in POLRI_TERMS:

        if contains_word(
            text,
            term
        ):

            polri_hits.append(
                term
            )

    # Tidak ada hubungan dengan polisi.
    if not polri_hits:

        return {
            "relevance": "low",
            "scope": "neutral",
            "category": "Tidak Relevan",
            "score": 0,
        }

    # --------------------------------------------------------
    # NOISE
    # --------------------------------------------------------

    noise_hits = []

    for term in NOISE_TERMS:

        if contains_word(
            text,
            term
        ):

            noise_hits.append(
                term
            )

    if (
        noise_hits
        and len(polri_hits) <= 1
    ):

        return {
            "relevance": "noise",
            "scope": "noise",
            "category": "Tidak Relevan",
            "score": 0,
        }

    # --------------------------------------------------------
    # POLISI SEBAGAI KORBAN
    #
    # HARUS diperiksa SEBELUM negative.
    # --------------------------------------------------------

    police_is_victim = any(
        re.search(
            pattern,
            text
        )
        for pattern
        in POLICE_VICTIM_PATTERNS
    )

    if police_is_victim:

        return {
            "relevance": "high",
            "scope": "incident",
            "category":
                "Peristiwa Melibatkan Polisi",
            "score": 70,
        }

    # --------------------------------------------------------
    # POLISI SEBAGAI PELAKU
    # --------------------------------------------------------

    police_is_negative = any(
        re.search(
            pattern,
            text
        )
        for pattern
        in POLICE_NEGATIVE_PATTERNS
    )

    if police_is_negative:

        # Narkoba
        if any(
            contains_word(
                text,
                term
            )
            for term in [
                "narkoba",
                "narkotika",
                "sabu",
                "ganja",
            ]
        ):

            category = (
                "Oknum / Narkoba"
            )

        # Korupsi / Suap / Pungli
        elif any(
            contains_word(
                text,
                term
            )
            for term in [
                "korupsi",
                "suap",
                "pungli",
                "pemerasan",
            ]
        ):

            category = (
                "Oknum / Korupsi / Pungli"
            )

        # Etik / Disiplin
        elif any(
            contains_word(
                text,
                term
            )
            for term in [
                "etik",
                "disiplin",
            ]
        ):

            category = (
                "Etik / Disiplin"
            )

        # Kekerasan
        elif any(
            contains_word(
                text,
                term
            )
            for term in [
                "penganiayaan",
                "kekerasan",
                "penembakan",
            ]
        ):

            category = (
                "Kekerasan / Penganiayaan"
            )

        # Penyalahgunaan wewenang
        elif contains_word(
            text,
            "penyalahgunaan wewenang"
        ):

            category = (
                "Penyalahgunaan Wewenang"
            )

        else:

            category = (
                "Oknum / Pelanggaran Anggota"
            )

        return {
            "relevance": "high",
            "scope": "negative",
            "category": category,
            "score": 100,
        }

    # --------------------------------------------------------
    # POLISI SEBAGAI PENINDAK
    # --------------------------------------------------------

    police_is_actor = any(
        contains_word(
            text,
            term
        )
        for term in CASE_ACTION_TERMS
    )

    if police_is_actor:

        return {
            "relevance": "high",
            "scope": "case",
            "category": "Ungkap Kasus",
            "score": 60,
        }

    # --------------------------------------------------------
    # BERITA POLISI LAINNYA
    # --------------------------------------------------------

    return {
        "relevance": "medium",
        "scope": "neutral",
        "category":
            "Berita Polisi Lainnya",
        "score": 25,
    }


# ============================================================
# PRIORITY
# ============================================================

def detect_priority(
    classification,
    title,
    description
):

    if classification["scope"] != "negative":

        return "low"

    text = normalize(
        title
        + " "
        + description
    )

    high_terms = [
        "korupsi",
        "suap",
        "pungli",
        "pemerasan",
        "narkoba",
        "narkotika",
        "sabu",
        "penembakan",
        "tewas",
        "meninggal",
    ]

    medium_terms = [
        "diduga",
        "pelanggaran etik",
        "pelanggaran disiplin",
        "penganiayaan",
        "kekerasan",
        "tersangka",
        "ditangkap",
        "ditahan",
    ]

    if any(
        contains_word(
            text,
            term
        )
        for term in high_terms
    ):

        return "high"

    if any(
        contains_word(
            text,
            term
        )
        for term in medium_terms
    ):

        return "medium"

    return "low"


# ============================================================
# YOUTUBE API
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

        raise RuntimeError(
            "YouTube API HTTP "
            + str(e.code)
            + ": "
            + body
        )

    except URLError as e:

        raise RuntimeError(
            "YouTube network error: "
            + str(e)
        )


# ============================================================
# LOAD EXISTING
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

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    if not API_KEY:

        raise RuntimeError(
            "YOUTUBE_API_KEY tidak tersedia."
        )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    published_after = (
        now - timedelta(
            days=2
        )
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # --------------------------------------------------------
    # OLD DATA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    added = 0

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

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

            # ------------------------------------------------
            # CLASSIFY
            # ------------------------------------------------

            classification = classify_content(
                title,
                description
            )

            # ------------------------------------------------
            # LOCATION
            # ------------------------------------------------

            location = detect_location(
                title,
                description
            )

            # ------------------------------------------------
            # PRIORITY
            # ------------------------------------------------

            priority = detect_priority(
                classification,
                title,
                description
            )

            # ------------------------------------------------
            # RECORD
            # ------------------------------------------------

            item = {

                "id":
                    make_id(
                        video_id
                    ),

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

                # Classification
                "relevance":
                    classification[
                        "relevance"
                    ],

                "scope":
                    classification[
                        "scope"
                    ],

                "category":
                    classification[
                        "category"
                    ],

                "classification_score":
                    classification[
                        "score"
                    ],

                # Location
                "is_jatim":
                    location[
                        "is_jatim"
                    ],

                "region":
                    (
                        "Jawa Timur"
                        if location[
                            "is_jatim"
                        ]
                        else "Indonesia"
                    ),

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

                # Priority
                "priority":
                    priority,

                # Timestamp
                "collected_at":
                    now.isoformat(),
            }

            # ------------------------------------------------
            # UPDATE / INSERT
            # ------------------------------------------------

            if video_id in items_by_video:

                items_by_video[
                    video_id
                ].update(
                    item
                )

            else:

                items_by_video[
                    video_id
                ] = item

                added += 1

    # ========================================================
    # SORT
    # ========================================================

    items = list(
        items_by_video.values()
    )

    items.sort(
        key=lambda item:
            item.get(
                "published_at",
                ""
            ),
        reverse=True
    )

    # Maksimum histori.
    items = items[:1500]

    # ========================================================
    # STATISTICS
    # ========================================================

    stats = {

        "total":
            len(items),

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

    # ========================================================
    # OUTPUT
    # ========================================================

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

    # ========================================================
    # LOG
    # ========================================================

    print(
        "========================================"
    )

    print(
        f"New videos       : {added}"
    )

    print(
        f"Total videos     : {stats['total']}"
    )

    print(
        f"Jawa Timur       : {stats['jatim']}"
    )

    print(
        f"Negative Polri   : {stats['negative']}"
    )

    print(
        f"Peristiwa        : {stats['incident']}"
    )

    print(
        f"Ungkap kasus     : {stats['case']}"
    )

    print(
        f"Netral           : {stats['neutral']}"
    )

    print(
        f"Noise            : {stats['noise']}"
    )

    print(
        f"Prioritas tinggi : {stats['high_priority']}"
    )

    print(
        f"Output           : {OUT}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":

    main()
