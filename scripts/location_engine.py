import re


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


# Lokasi Jawa Timur.
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


# Lokasi luar Jatim yang perlu menjadi guard.
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


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_word(text, term):
    text = normalize(text)
    term = normalize(term)

    return re.search(
        r"(?<![a-z0-9])"
        + re.escape(term)
        + r"(?![a-z0-9])",
        text,
    ) is not None


def detect_polres(text):
    matches = []

    for polres, aliases in POLRES_MAP.items():
        for alias in aliases:
            if contains_word(text, alias):
                explicit = 1 if alias.startswith((
                    "polres ",
                    "polresta ",
                    "polrestabes ",
                )) else 0
                matches.append(
                    (
                        explicit,
                        len(alias),
                        polres,
                        alias,
                    )
                )

    if not matches:
        return None, None

    matches.sort(reverse=True)

    explicit, _, polres, evidence = matches[0]

    # A bare city name is a location signal, not proof that the
    # corresponding Polres is the operational Polres.
    if explicit == 0:
        return None, evidence

    return polres, evidence


def detect_location(title, description):
    title = normalize(title)
    description = normalize(description)

    text = f"{title} {description}"

    evidence = []
    score = 0
    source = None

    # --------------------------------------------------------
    # POLRES
    # --------------------------------------------------------

    polres, polres_evidence = detect_polres(text)

    if polres:
        score += 100
        evidence.append(polres_evidence)
        source = "polres"

    # --------------------------------------------------------
    # JAWA TIMUR EXPLICIT
    # --------------------------------------------------------

    if (
        contains_word(text, "jawa timur")
        or contains_word(text, "jatim")
    ):
        score += 80
        evidence.append("Jawa Timur/Jatim")

        if source is None:
            source = "province"

    # --------------------------------------------------------
    # LOCALITY
    # --------------------------------------------------------

    for location in JATIM_LOCATIONS:
        if contains_word(text, location):

            if contains_word(title, location):
                score += 60
            else:
                score += 35

            evidence.append(location)

            if source is None:
                source = "location"

    # --------------------------------------------------------
    # OUTSIDE GUARD
    #
    # Penting:
    # "Batu" tidak boleh match "Baturaja".
    # --------------------------------------------------------

    outside = []

    for location in OUTSIDE_LOCATIONS:
        if contains_word(text, location):
            outside.append(location)

    if outside and not polres:
        score -= 100

        for location in outside:
            evidence.append(
                "LUAR:" + location
            )

        if source is None:
            source = "outside"

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    is_jatim = score >= 35

    if outside and not polres and score < 80:
        is_jatim = False

    confidence = max(
        0,
        min(100, score),
    )

    return {
        "is_jatim": is_jatim,
        "region": (
            "Jawa Timur"
            if is_jatim
            else "Indonesia"
        ),
        "polres": polres,
        "confidence": confidence,
        "source": source,
        "evidence": evidence,
    }
