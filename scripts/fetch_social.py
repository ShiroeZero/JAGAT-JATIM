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
# 39 POLRES / SATWIL JAWA TIMUR
# ============================================================

POLRES_MAP = {
    "POLRES PELABUHAN TANJUNG PERAK": ["pelabuhan tanjung perak", "tanjung perak"],
    "POLRES JEMBER": ["polres jember", "kabupaten jember", "jember"],
    "POLRES KEDIRI": ["polres kediri", "kabupaten kediri"],
    "POLRES BLITAR KOTA": ["polres blitar kota", "blitar kota"],
    "POLRESTABES SURABAYA": ["polrestabes surabaya", "surabaya"],
    "POLRESTA MALANG KOTA": ["polresta malang kota", "malang kota"],
    "POLRESTA SIDOARJO": ["polresta sidoarjo", "sidoarjo"],
    "POLRESTA BANYUWANGI": ["polresta banyuwangi", "banyuwangi"],
    "POLRESTA TUBAN": ["polresta tuban", "tuban"],
    "POLRESTA SUMENEP": ["polresta sumenep", "sumenep"],
    "POLRES GRESIK": ["polres gresik", "gresik"],
    "POLRES MALANG": ["polres malang", "kabupaten malang"],
    "POLRES PASURUAN": ["polres pasuruan", "kabupaten pasuruan"],
    "POLRES PASURUAN KOTA": ["polres pasuruan kota", "pasuruan kota"],
    "POLRES PROBOLINGGO": ["polres probolinggo", "kabupaten probolinggo"],
    "POLRES PROBOLINGGO KOTA": ["polres probolinggo kota", "probolinggo kota"],
    "POLRES LUMAJANG": ["polres lumajang", "lumajang"],
    "POLRES BATU": ["polres batu", "kota batu"],
    "POLRES BONDOWOSO": ["polres bondowoso", "bondowoso"],
    "POLRES SITUBONDO": ["polres situbondo", "situbondo"],
    "POLRES KEDIRI KOTA": ["polres kediri kota", "kediri kota"],
    "POLRES TULUNGAGUNG": ["polres tulungagung", "tulungagung"],
    "POLRES NGANJUK": ["polres nganjuk", "nganjuk"],
    "POLRES TRENGGALEK": ["polres trenggalek", "trenggalek"],
    "POLRES BLITAR": ["polres blitar", "kabupaten blitar"],
    "POLRES MADIUN": ["polres madiun", "kabupaten madiun"],
    "POLRES MADIUN KOTA": ["polres madiun kota", "madiun kota"],
    "POLRES NGAWI": ["polres ngawi", "ngawi"],
    "POLRES MAGETAN": ["polres magetan", "magetan"],
    "POLRES PONOROGO": ["polres ponorogo", "ponorogo"],
    "POLRES PACITAN": ["polres pacitan", "pacitan"],
    "POLRES BOJONEGORO": ["polres bojonegoro", "bojonegoro"],
    "POLRES LAMONGAN": ["polres lamongan", "lamongan"],
    "POLRES MOJOKERTO": ["polres mojokerto", "kabupaten mojokerto"],
    "POLRES MOJOKERTO KOTA": ["polres mojokerto kota", "mojokerto kota"],
    "POLRES JOMBANG": ["polres jombang", "jombang"],
    "POLRES PAMEKASAN": ["polres pamekasan", "pamekasan"],
    "POLRES BANGKALAN": ["polres bangkalan", "bangkalan"],
    "POLRES SAMPANG": ["polres sampang", "sampang"],
}


# ============================================================
# KOTA / KABUPATEN JAWA TIMUR
# ============================================================

JATIM_LOCATIONS = {
    "Surabaya",
    "Sidoarjo",
    "Gresik",
    "Lamongan",
    "Tuban",
    "Bojonegoro",
    "Ngawi",
    "Magetan",
    "Madiun",
    "Ponorogo",
    "Pacitan",
    "Nganjuk",
    "Kediri",
    "Tulungagung",
    "Blitar",
    "Trenggalek",
    "Malang",
    "Batu",
    "Pasuruan",
    "Probolinggo",
    "Lumajang",
    "Jember",
    "Bondowoso",
    "Situbondo",
    "Banyuwangi",
    "Mojokerto",
    "Jombang",
    "Pamekasan",
    "Bangkalan",
    "Sampang",
    "Sumenep",
    "Madura",
}


# ============================================================
# WILAYAH LUAR JATIM YANG SERING MUNCUL
# Dipakai sebagai negative evidence.
# ============================================================

OUTSIDE_LOCATIONS = {
    "Riau",
    "Pekanbaru",
    "Lampung",
    "Lampung Utara",
    "Bandar Lampung",
    "Sumatera Selatan",
    "Palembang",
    "Baturaja",
    "OKU",
    "OKU Timur",
    "Jakarta",
    "Jakarta Barat",
    "Jakarta Timur",
    "Jakarta Selatan",
    "Jakarta Utara",
    "Tangerang",
    "Tangerang Selatan",
    "Banten",
    "Bandung",
    "Jawa Barat",
    "Jawa Tengah",
    "Semarang",
    "Yogyakarta",
    "DIY",
    "Bali",
    "Denpasar",
    "Pontianak",
    "Kalimantan",
    "Sulawesi",
    "Morowali",
    "Padang",
    "Sumatera Barat",
    "Batam",
    "Kepulauan Riau",
}


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
# RELEVANSI TERHADAP POLRI
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
    "ditangkap",
    "ditahan",
    "tersangka",
    "terlibat",
    "diduga",
    "pelanggaran etik",
    "pelanggaran disiplin",
    "penganiayaan",
    "kekerasan",
    "penembakan",
    "pemerasan",
    "pungli",
    "suap",
    "korupsi",
    "narkoba",
    "sabu",
    "narkotika",
    "penyalahgunaan wewenang",
    "melanggar",
]


# Berita yang menggunakan polisi sebagai pelaku tindakan
# kriminal biasa tidak otomatis dianggap negatif terhadap polisi.

POLICE_NEGATIVE_PATTERNS = [
    r"oknum\s+(polisi|polri)",
    r"anggota\s+(polisi|polri).{0,80}(ditangkap|ditahan|tersangka|diduga|terlibat)",
    r"(polisi|polri).{0,80}(ditangkap|ditahan|tersangka|diduga|terlibat)",
    r"(polisi|polri).{0,80}(pungli|suap|korupsi|pemerasan)",
    r"(polisi|polri).{0,80}(narkoba|narkotika|sabu)",
    r"(polisi|polri).{0,80}(penganiayaan|kekerasan|penembakan)",
    r"(polisi|polri).{0,80}(pelanggaran\s+etik|pelanggaran\s+disiplin)",
    r"(polisi|polri).{0,80}(penyalahgunaan\s+wewenang)",
]


# ============================================================
# UNGkap kasus oleh polisi
# ============================================================

CASE_ACTION_TERMS = [
    "polisi menangkap",
    "polisi ungkap",
    "polisi mengungkap",
    "polisi amankan",
    "polisi berhasil menangkap",
    "polisi berhasil mengungkap",
    "ditangkap polisi",
    "diamankan polisi",
]


# ============================================================
# GENERIC / NOISE CONTENT
# ============================================================

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


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"&amp;", " dan ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def words_in(text, terms):
    text = normalize(text)
    return [term for term in terms if term in text]


def make_id(video_id):
    return hashlib.sha1(
        f"youtube|{video_id}".encode("utf-8")
    ).hexdigest()


# ============================================================
# LOCATION DETECTION
# ============================================================

def detect_polres(text):
    text = normalize(text)

    candidates = []

    for polres, aliases in POLRES_MAP.items():
        for alias in aliases:
            if alias in text:
                candidates.append(
                    (len(alias), polres, alias)
                )

    if not candidates:
        return None, None

    candidates.sort(reverse=True)

    _, polres, evidence = candidates[0]

    return polres, evidence


def detect_jatim_location(text):
    text = normalize(text)

    found = []

    for location in JATIM_LOCATIONS:
        if normalize(location) in text:
            found.append(location)

    return found


def detect_outside_location(text):
    text = normalize(text)

    found = []

    for location in OUTSIDE_LOCATIONS:
        if normalize(location) in text:
            found.append(location)

    return found


def location_score(title, description):
    title_n = normalize(title)
    desc_n = normalize(description)

    combined = f"{title_n} {desc_n}"

    score = 0
    evidence = []
    source = None

    # --------------------------------------------------------
    # Polres = bukti terkuat
    # --------------------------------------------------------

    polres, polres_evidence = detect_polres(
        combined
    )

    if polres:
        score += 100
        evidence.append(polres_evidence)
        source = "polres"

    # --------------------------------------------------------
    # Provinsi eksplisit
    # --------------------------------------------------------

    if "jawa timur" in combined or "jatim" in combined:
        score += 80
        evidence.append(
            "Jawa Timur/Jatim"
        )

        if source is None:
            source = "province"

    # --------------------------------------------------------
    # Kota/kabupaten Jatim
    # --------------------------------------------------------

    jatim_locations = detect_jatim_location(
        combined
    )

    if jatim_locations:
        # Judul diberi bobot lebih besar.
        for location in jatim_locations:
            if normalize(location) in title_n:
                score += 60
            else:
                score += 35

            evidence.append(location)

        if source is None:
            source = "location"

    # --------------------------------------------------------
    # Explicit outside-Jatim
    # --------------------------------------------------------

    outside = detect_outside_location(
        combined
    )

    if outside and not polres:
        score -= 90

        evidence.extend(
            [f"LUAR:{x}" for x in outside]
        )

        if source is None:
            source = "outside"

    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    is_jatim = score >= 35

    # Jika bukti luar Jatim sangat kuat,
    # jangan biarkan keyword umum mengalahkannya.

    if outside and not polres:
        if score < 80:
            is_jatim = False

    confidence = min(
        100,
        max(0, score)
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

def classify_content(title, description):

    title_n = normalize(title)
    desc_n = normalize(description)
    text = f"{title_n} {desc_n}"

    polri_hits = words_in(
        text,
        POLRI_TERMS
    )

    negative_hits = words_in(
        text,
        NEGATIVE_TERMS
    )

    noise_hits = words_in(
        text,
        NOISE_TERMS
    )

    # --------------------------------------------------------
    # Noise
    # --------------------------------------------------------

    if noise_hits and len(polri_hits) <= 1:
        return {
            "relevance": "noise",
            "scope": "neutral",
            "category": "Tidak Relevan",
            "score": 0,
        }

    # --------------------------------------------------------
    # Tidak ada hubungan Polri
    # --------------------------------------------------------

    if not polri_hits:
        return {
            "relevance": "low",
            "scope": "neutral",
            "category": "Tidak Relevan",
            "score": 0,
        }

    # --------------------------------------------------------
    # Negative terhadap polisi
    # --------------------------------------------------------

    negative_pattern = any(
        re.search(
            pattern,
            text
        )
        for pattern in POLICE_NEGATIVE_PATTERNS
    )

    if negative_pattern:
        if any(
            x in text
            for x in [
                "narkoba",
                "narkotika",
                "sabu",
                "ganja",
            ]
        ):
            category = "Oknum / Narkoba"

        elif any(
            x in text
            for x in [
                "korupsi",
                "suap",
                "pungli",
                "pemerasan",
            ]
        ):
            category = "Oknum / Korupsi / Pungli"

        elif any(
            x in text
            for x in [
                "etik",
                "disiplin",
            ]
        ):
            category = "Etik / Disiplin"

        elif any(
            x in text
            for x in [
                "penganiayaan",
                "kekerasan",
                "penembakan",
            ]
        ):
            category = "Kekerasan / Penganiayaan"

        elif "penyalahgunaan wewenang" in text:
            category = "Penyalahgunaan Wewenang"

        else:
            category = "Oknum / Pelanggaran Anggota"

        return {
            "relevance": "high",
            "scope": "negative",
            "category": category,
            "score": 100,
        }

    # --------------------------------------------------------
    # Ungkap kasus oleh polisi
    # --------------------------------------------------------

    if any(
        term in text
        for term in CASE_ACTION_TERMS
    ):
        return {
            "relevance": "high",
            "scope": "case",
            "category": "Ungkap Kasus",
            "score": 60,
        }

    # --------------------------------------------------------
    # Polisi disebut tetapi tidak jelas arahnya
    # --------------------------------------------------------

    return {
        "relevance": "medium",
        "scope": "neutral",
        "category": "Berita Polisi Lainnya",
        "score": 25,
    }


# ============================================================
# PRIORITY
# ============================================================

def priority_for(classification, title, description):

    text = normalize(
        f"{title} {description}"
    )

    if classification["scope"] != "negative":
        return "low"

    very_high = [
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

    medium = [
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
        term in text
        for term in very_high
    ):
        return "high"

    if any(
        term in text
        for term in medium
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
            f"YouTube API HTTP {e.code}: {body}"
        )

    except URLError as e:

        raise RuntimeError(
            f"YouTube network error: {e}"
        )


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

    print("========================================")
    print("PNM — YOUTUBE SOCIAL MONITOR")
    print("========================================")

    if not API_KEY:
        raise RuntimeError(
            "YOUTUBE_API_KEY tidak tersedia."
        )

    now = datetime.now(
        timezone.utc
    )

    # Overlap 48 jam supaya collector yang gagal
    # satu siklus tidak langsung kehilangan data.

    published_after = (
        now - timedelta(days=2)
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

    # Statistik
    negative_count = 0
    case_count = 0
    jatim_count = 0
    noise_count = 0

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

            classification = classify_content(
                title,
                description
            )

            location = location_score(
                title,
                description
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Channel TIDAK digunakan untuk menentukan Jatim.
            # ------------------------------------------------

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
                    description[:1200],

                "relevance":
                    classification["relevance"],

                "scope":
                    classification["scope"],

                "category":
                    classification["category"],

                "classification_score":
                    classification["score"],

                "is_jatim":
                    location["is_jatim"],

                "region":
                    (
                        "Jawa Timur"
                        if location["is_jatim"]
                        else "Indonesia"
                    ),

                "polres":
                    location["polres"],

                "location_confidence":
                    location["confidence"],

                "location_source":
                    location["source"],

                "location_evidence":
                    location["evidence"],

                "priority":
                    priority_for(
                        classification,
                        title,
                        description
                    ),

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

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

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

    # Jangan biarkan file tumbuh tanpa batas.
    items = items[:1500]

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    for item in items:

        if item.get("is_jatim"):
            jatim_count += 1

        if item.get("scope") == "negative":
            negative_count += 1

        if item.get("scope") == "case":
            case_count += 1

        if item.get("relevance") == "noise":
            noise_count += 1

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output = {

        "generated_at":
            now.isoformat(),

        "platform":
            "YouTube",

        "total":
            len(items),

        "statistics": {

            "new_videos":
                added,

            "jatim":
                jatim_count,

            "negative":
                negative_count,

            "case":
                case_count,

            "noise":
                noise_count,
        },

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

    print("========================================")
    print(f"New videos     : {added}")
    print(f"Total videos   : {len(items)}")
    print(f"Jawa Timur     : {jatim_count}")
    print(f"Negative Polri : {negative_count}")
    print(f"Ungkap kasus   : {case_count}")
    print(f"Noise          : {noise_count}")
    print(f"Output         : {OUT}")
    print("========================================")


if __name__ == "__main__":
    main()
