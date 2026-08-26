import json
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# PNM — YOUTUBE SOCIAL MONITOR
# CLASSIFIER V3
#
# Prioritas:
# 1. Noise
# 2. Polisi sebagai korban
# 3. Polisi sebagai penindak
# 4. Polisi sebagai pelaku
# 5. Berita polisi umum
# 6. Review / ambiguous
#
# Channel TIDAK digunakan sebagai penentu lokasi.
# ============================================================

OUT = "data/social.json"
API_URL = "https://www.googleapis.com/youtube/v3/search"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()


# ============================================================
# 39 POLRES JAWA TIMUR
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
# LOKASI JAWA TIMUR
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
# QUERY
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
# TERM
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


# ============================================================
# POLISI SEBAGAI KORBAN
# ============================================================

VICTIM_PATTERNS = [

    r"\bpolisi\b.{0,100}\b(ditembak|tertembak)\b",

    r"\bpolisi\b.{0,100}\b(dis(t)?erang|diserang)\b",

    r"\bpolisi\b.{0,100}\b(dianiaya|dikeroyok)\b",

    r"\bpolisi\b.{0,100}\b(terluka|luka)\b",

    r"\bpolisi\b.{0,100}\b(tewas|meninggal)\b",

    r"\banggota polisi\b.{0,100}"
    r"\b(ditembak|terluka|tewas|meninggal)\b",

    r"\banggota polri\b.{0,100}"
    r"\b(ditembak|terluka|tewas|meninggal)\b",

    r"\bpolisi\b.{0,100}"
    r"\bmenjadi korban\b",

    r"\bpolisi\b.{0,100}"
    r"\bjadi korban\b",

    r"\bpolisi\b.{0,100}"
    r"\bbaku tembak\b",
]


# ============================================================
# POLISI SEBAGAI PENINDAK
# ============================================================

LAW_ENFORCEMENT_PATTERNS = [

    r"\bditangkap oleh polisi\b",

    r"\bditangkap polisi\b",

    r"\bdiamankan oleh polisi\b",

    r"\bdiamankan polisi\b",

    r"\bditangkap polri\b",

    r"\bdiamankan polri\b",

    r"\bpolisi menangkap\b",

    r"\bpolisi mengamankan\b",

    r"\bpolisi amankan\b",

    r"\bpolisi mengungkap\b",

    r"\bpolisi ungkap\b",

    r"\bpolisi menyita\b",

    r"\bpolisi sita\b",

    r"\bpolisi menggagalkan\b",

    r"\bpolisi membekuk\b",

    r"\bpolisi berhasil menangkap\b",

    r"\bpolisi berhasil mengungkap\b",
]


# ============================================================
# POLISI SEBAGAI PELAKU
# ============================================================

POLICE_OFFENDER_PATTERNS = [

    r"\boknum polisi\b",

    r"\boknum polri\b",

    r"\banggota polisi\b.{0,100}"
    r"\b(tersangka|terlibat|diduga|ditangkap|ditahan)\b",

    r"\banggota polri\b.{0,100}"
    r"\b(tersangka|terlibat|diduga|ditangkap|ditahan)\b",

    r"\bpolisi\b.{0,80}"
    r"\bjadi tersangka\b",

    r"\bpolisi\b.{0,80}"
    r"\bmenjadi tersangka\b",

    r"\bpolisi\b.{0,80}"
    r"\bterlibat korupsi\b",

    r"\bpolisi\b.{0,80}"
    r"\bterlibat suap\b",

    r"\bpolisi\b.{0,80}"
    r"\bterlibat pungli\b",

    r"\bpolisi\b.{0,80}"
    r"\bterlibat narkoba\b",

    r"\bpolisi\b.{0,80}"
    r"\bterlibat narkotika\b",

    r"\bpolisi\b.{0,80}"
    r"\bmelakukan penganiayaan\b",

    r"\bpolisi\b.{0,80}"
    r"\bmelakukan kekerasan\b",

    r"\bpolisi\b.{0,80}"
    r"\bmelakukan pungli\b",

    r"\bpolisi\b.{0,80}"
    r"\bmelakukan pemerasan\b",

    r"\bpolisi\b.{0,100}"
    r"\bpelanggaran etik\b",

    r"\bpolisi\b.{0,100}"
    r"\bpelanggaran disiplin\b",

    r"\bpolisi\b.{0,100}"
    r"\bpenyalahgunaan wewenang\b",
]


# ============================================================
# NEGATIVE KEYWORDS
# ============================================================

NEGATIVE_KEYWORDS = [
    "korupsi",
    "suap",
    "pungli",
    "pemerasan",
    "narkoba",
    "narkotika",
    "sabu",
    "pelanggaran etik",
    "pelanggaran disiplin",
    "penyalahgunaan wewenang",
    "penganiayaan",
    "kekerasan",
]


# ============================================================
# WORD MATCH
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


def contains_word(
    text,
    term
):

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
# MATCH PATTERN
# ============================================================

def match_patterns(
    text,
    patterns
):

    for pattern in patterns:

        if re.search(
            pattern,
            text
        ):

            return True

    return False


# ============================================================
# LOCATION
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

    candidates.sort(
        reverse=True
    )

    _, polres, evidence = candidates[0]

    return polres, evidence


def detect_locations(
    text,
    locations
):

    found = []

    for location in locations:

        if contains_word(
            text,
            location
        ):

            found.append(
                location
            )

    return found


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

    # --------------------------------------------------------
    # POLRES
    # --------------------------------------------------------

    polres, polres_evidence = detect_polres(
        combined
    )

    if polres:

        score += 100

        evidence.append(
            polres_evidence
        )

        source = "polres"

    # --------------------------------------------------------
    # PROVINCE
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
    # JATIM LOCATIONS
    # --------------------------------------------------------

    jatim = detect_locations(
        combined,
        JATIM_LOCATIONS
    )

    for location in jatim:

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
    # OUTSIDE
    # --------------------------------------------------------

    outside = detect_locations(
        combined,
        OUTSIDE_LOCATIONS
    )

    if outside and not polres:

        score -= 100

        for location in outside:

            evidence.append(
                "LUAR:" + location
            )

        if source is None:

            source = "outside"

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    is_jatim = score >= 35

    if (
        outside
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
# ROLE CLASSIFIER
# ============================================================

def classify_role(
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
    # 1. NOISE
    # --------------------------------------------------------

    noise_hits = [
        term
        for term in NOISE_TERMS
        if contains_word(
            text,
            term
        )
    ]

    if noise_hits:

        return {
            "scope": "noise",
            "category": "Tidak Relevan",
            "role": "noise",
            "confidence": 95,
            "reason": noise_hits,
        }

    # --------------------------------------------------------
    # 2. POLICE VICTIM
    # --------------------------------------------------------

    if match_patterns(
        text,
        VICTIM_PATTERNS
    ):

        return {
            "scope": "incident",
            "category":
                "Peristiwa Melibatkan Polisi",
            "role": "victim",
            "confidence": 95,
            "reason": [
                "polisi sebagai korban"
            ],
        }

    # --------------------------------------------------------
    # 3. LAW ENFORCEMENT
    #
    # Diperiksa SEBELUM offender.
    #
    # Contoh:
    # "kurir narkoba ditangkap polisi"
    #
    # harus CASE.
    # --------------------------------------------------------

    if match_patterns(
        text,
        LAW_ENFORCEMENT_PATTERNS
    ):

        return {
            "scope": "case",
            "category": "Ungkap Kasus",
            "role": "enforcer",
            "confidence": 95,
            "reason": [
                "polisi sebagai penindak"
            ],
        }

    # --------------------------------------------------------
    # 4. POLICE OFFENDER
    # --------------------------------------------------------

    if match_patterns(
        text,
        POLICE_OFFENDER_PATTERNS
    ):

        keyword_hits = [
            term
            for term in NEGATIVE_KEYWORDS
            if contains_word(
                text,
                term
            )
        ]

        if (
            "narkoba" in keyword_hits
            or "narkotika" in keyword_hits
            or "sabu" in keyword_hits
        ):

            category = (
                "Oknum / Narkoba"
            )

        elif (
            "korupsi" in keyword_hits
            or "suap" in keyword_hits
            or "pungli" in keyword_hits
            or "pemerasan" in keyword_hits
        ):

            category = (
                "Oknum / Korupsi / Pungli"
            )

        elif (
            "pelanggaran etik"
            in keyword_hits
            or
            "pelanggaran disiplin"
            in keyword_hits
        ):

            category = (
                "Etik / Disiplin"
            )

        elif (
            "penganiayaan"
            in keyword_hits
            or
            "kekerasan"
            in keyword_hits
        ):

            category = (
                "Kekerasan / Penganiayaan"
            )

        elif (
            "penyalahgunaan wewenang"
            in keyword_hits
        ):

            category = (
                "Penyalahgunaan Wewenang"
            )

        else:

            category = (
                "Oknum / Pelanggaran Anggota"
            )

        return {
            "scope": "negative",
            "category": category,
            "role": "offender",
            "confidence": 90,
            "reason": keyword_hits,
        }

    # --------------------------------------------------------
    # 5. GENERAL POLICE NEWS
    # --------------------------------------------------------

    has_polri = any(
        contains_word(
            text,
            term
        )
        for term in POLRI_TERMS
    )

    if has_polri:

        return {
            "scope": "neutral",
            "category":
                "Berita Polisi Lainnya",
            "role": "general",
            "confidence": 65,
            "reason": [
                "polisi disebut"
            ],
        }

    # --------------------------------------------------------
    # 6. REVIEW
    # --------------------------------------------------------

    return {
        "scope": "review",
        "category": "Perlu Review",
        "role": "ambiguous",
        "confidence": 40,
        "reason": [
            "hubungan tidak cukup jelas"
        ],
    }


# ============================================================
# PRIORITY
# ============================================================

def detect_priority(
    classification,
    title,
    description
):

    if classification[
        "scope"
    ] != "negative":

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
        "tewas",
        "meninggal",
        "penembakan",
    ]

    medium_terms = [
        "tersangka",
        "ditangkap",
        "ditahan",
        "diduga",
        "pelanggaran etik",
        "pelanggaran disiplin",
        "penganiayaan",
        "kekerasan",
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
# EXISTING DATA
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
        "PNM — YOUTUBE SOCIAL MONITOR V3"
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
        - timedelta(
            days=2
        )
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

            # ------------------------------------------------
            # CLASSIFICATION
            # ------------------------------------------------

            classification = classify_role(
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
            # ITEM
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

                # --------------------------------------------
                # ROLE / CLASSIFICATION
                # --------------------------------------------

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

                # --------------------------------------------
                # LOCATION
                # --------------------------------------------

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

                # --------------------------------------------
                # PRIORITY
                # --------------------------------------------

                "priority":
                    priority,

                "collected_at":
                    now.isoformat(),
            }

            # ------------------------------------------------
            # UPDATE EXISTING
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
        key=lambda x:
            x.get(
                "published_at",
                ""
            ),
        reverse=True
    )

    # Keep max 1500 videos.
    items = items[:1500]

    # ========================================================
    # STATISTICS
    # ========================================================

    stats = {

        "total":
            len(items),

        "new_videos":
            added,

        "jatim":
            sum(
                1
                for x in items
                if x.get(
                    "is_jatim"
                )
            ),

        "negative":
            sum(
                1
                for x in items
                if x.get(
                    "scope"
                ) == "negative"
            ),

        "incident":
            sum(
                1
                for x in items
                if x.get(
                    "scope"
                ) == "incident"
            ),

        "case":
            sum(
                1
                for x in items
                if x.get(
                    "scope"
                ) == "case"
            ),

        "neutral":
            sum(
                1
                for x in items
                if x.get(
                    "scope"
                ) == "neutral"
            ),

        "review":
            sum(
                1
                for x in items
                if x.get(
                    "scope"
                ) == "review"
            ),

        "noise":
            sum(
                1
                for x in items
                if x.get(
                    "scope"
                ) == "noise"
            ),

        "high_priority":
            sum(
                1
                for x in items
                if x.get(
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
        f"New videos       : {stats['new_videos']}"
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
        f"Review           : {stats['review']}"
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
