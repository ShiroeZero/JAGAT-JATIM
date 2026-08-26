import re


# ============================================================
# CANONICAL 39 POLRES JAWA TIMUR
# ============================================================

POLRES_MAP = {
    "POLRES PELABUHAN TANJUNG PERAK": [
        "polres pelabuhan tanjung perak",
        "polres tanjung perak",
    ],
    "POLRES JEMBER": [
        "polres jember",
        "kepolisian resor jember",
    ],
    "POLRES KEDIRI": [
        "polres kediri",
        "kepolisian resor kediri",
    ],
    "POLRES BLITAR KOTA": [
        "polres blitar kota",
        "polresta blitar",
        "kepolisian resor blitar kota",
    ],
    "POLRESTABES SURABAYA": [
        "polrestabes surabaya",
        "polres kota besar surabaya",
    ],
    "POLRESTA MALANG KOTA": [
        "polresta malang kota",
        "polres malang kota",
        "kepolisian resor kota malang",
    ],
    "POLRESTA SIDOARJO": [
        "polresta sidoarjo",
        "kepolisian resor kota sidoarjo",
    ],
    "POLRESTA BANYUWANGI": [
        "polresta banyuwangi",
        "kepolisian resor kota banyuwangi",
    ],
    "POLRESTA TUBAN": [
        "polresta tuban",
        "kepolisian resor tuban",
    ],
    "POLRESTA SUMENEP": [
        "polresta sumenep",
        "kepolisian resor sumenep",
    ],
    "POLRES GRESIK": [
        "polres gresik",
        "kepolisian resor gresik",
    ],
    "POLRES MALANG": [
        "polres malang",
        "kepolisian resor malang",
    ],
    "POLRES PASURUAN": [
        "polres pasuruan",
        "kepolisian resor pasuruan",
    ],
    "POLRES PASURUAN KOTA": [
        "polres pasuruan kota",
        "polresta pasuruan",
        "kepolisian resor kota pasuruan",
    ],
    "POLRES PROBOLINGGO": [
        "polres probolinggo",
        "kepolisian resor probolinggo",
    ],
    "POLRES PROBOLINGGO KOTA": [
        "polres probolinggo kota",
        "polresta probolinggo",
        "kepolisian resor kota probolinggo",
    ],
    "POLRES LUMAJANG": [
        "polres lumajang",
        "kepolisian resor lumajang",
    ],
    "POLRES BATU": [
        "polres batu",
        "polresta batu",
        "kepolisian resor batu",
    ],
    "POLRES BONDOWOSO": [
        "polres bondowoso",
        "kepolisian resor bondowoso",
    ],
    "POLRES SITUBONDO": [
        "polres situbondo",
        "kepolisian resor situbondo",
    ],
    "POLRES KEDIRI KOTA": [
        "polres kediri kota",
        "polresta kediri",
        "kepolisian resor kediri kota",
    ],
    "POLRES TULUNGAGUNG": [
        "polres tulungagung",
        "kepolisian resor tulungagung",
    ],
    "POLRES NGANJUK": [
        "polres nganjuk",
        "kepolisian resor nganjuk",
    ],
    "POLRES TRENGGALEK": [
        "polres trenggalek",
        "kepolisian resor trenggalek",
    ],
    "POLRES BLITAR": [
        "polres blitar",
        "kepolisian resor blitar",
    ],
    "POLRES MADIUN": [
        "polres madiun",
        "kepolisian resor madiun",
    ],
    "POLRES MADIUN KOTA": [
        "polres madiun kota",
        "polresta madiun",
        "kepolisian resor kota madiun",
    ],
    "POLRES NGAWI": [
        "polres ngawi",
        "kepolisian resor ngawi",
    ],
    "POLRES MAGETAN": [
        "polres magetan",
        "kepolisian resor magetan",
    ],
    "POLRES PONOROGO": [
        "polres ponorogo",
        "kepolisian resor ponorogo",
    ],
    "POLRES PACITAN": [
        "polres pacitan",
        "kepolisian resor pacitan",
    ],
    "POLRES BOJONEGORO": [
        "polres bojonegoro",
        "kepolisian resor bojonegoro",
    ],
    "POLRES LAMONGAN": [
        "polres lamongan",
        "kepolisian resor lamongan",
    ],
    "POLRES MOJOKERTO": [
        "polres mojokerto",
        "kepolisian resor mojokerto",
    ],
    "POLRES MOJOKERTO KOTA": [
        "polres mojokerto kota",
        "polresta mojokerto",
        "kepolisian resor kota mojokerto",
    ],
    "POLRES JOMBANG": [
        "polres jombang",
        "kepolisian resor jombang",
    ],
    "POLRES PAMEKASAN": [
        "polres pamekasan",
        "kepolisian resor pamekasan",
    ],
    "POLRES BANGKALAN": [
        "polres bangkalan",
        "kepolisian resor bangkalan",
    ],
    "POLRES SAMPANG": [
        "polres sampang",
        "kepolisian resor sampang",
    ],
}

# Location names only; never read publisher/source here.
JATIM_LOCATIONS = [
    "surabaya", "sidoarjo", "gresik", "lamongan", "tuban", "bojonegoro",
    "ngawi", "magetan", "madiun", "ponorogo", "pacitan", "nganjuk",
    "kediri", "tulungagung", "trenggalek", "blitar", "malang", "batu",
    "pasuruan", "probolinggo", "lumajang", "jember", "bondowoso",
    "situbondo", "banyuwangi", "mojokerto", "jombang", "pamekasan",
    "bangkalan", "sampang", "sumenep", "madura",
]


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_word(text, term):
    text = normalize(text)
    term = normalize(term)
    return re.search(
        r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])",
        text,
    ) is not None


def strip_publisher_suffix(title, source=""):
    """Remove Google News publisher suffix before location analysis."""
    title = str(title or "").strip()
    source = str(source or "").strip()
    if source:
        pattern = r"\s+(?:-|–|—|\|)\s*" + re.escape(source) + r"\s*$"
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)
    return title.strip()


def detect_polres(title):
    matches = []
    for polres, aliases in POLRES_MAP.items():
        for alias in aliases:
            if contains_word(title, alias):
                matches.append((len(alias), polres, alias))
    if not matches:
        return None, None
    matches.sort(key=lambda x: x[0], reverse=True)
    _, polres, evidence = matches[0]
    return polres, evidence


def locality_from_polres(polres):
    text = normalize(polres)
    # Longer names first to avoid kota/kabupaten collisions.
    mapping = [
        ("surabaya", "Surabaya"), ("sidoarjo", "Sidoarjo"), ("gresik", "Gresik"),
        ("lamongan", "Lamongan"), ("tuban", "Tuban"), ("bojonegoro", "Bojonegoro"),
        ("ngawi", "Ngawi"), ("magetan", "Magetan"), ("madiun", "Madiun"),
        ("ponorogo", "Ponorogo"), ("pacitan", "Pacitan"), ("nganjuk", "Nganjuk"),
        ("kediri", "Kediri"), ("tulungagung", "Tulungagung"), ("trenggalek", "Trenggalek"),
        ("blitar", "Blitar"), ("malang", "Malang"), ("batu", "Batu"),
        ("pasuruan", "Pasuruan"), ("probolinggo", "Probolinggo"), ("lumajang", "Lumajang"),
        ("jember", "Jember"), ("bondowoso", "Bondowoso"), ("situbondo", "Situbondo"),
        ("banyuwangi", "Banyuwangi"), ("mojokerto", "Mojokerto"), ("jombang", "Jombang"),
        ("pamekasan", "Pamekasan"), ("bangkalan", "Bangkalan"), ("sampang", "Sampang"),
        ("sumenep", "Sumenep"),
    ]
    for key, value in mapping:
        if key in text:
            return value
    return ""


def detect_location(title, description="", source=""):
    """
    LOCATION IS DETERMINED FROM THE ARTICLE TITLE ONLY.
    Description/source are intentionally ignored for geography.
    """
    clean_title = strip_publisher_suffix(title, source)
    t = normalize(clean_title)

    evidence = []
    scores = []

    polres, polres_evidence = detect_polres(t)
    if polres:
        scores.append(100)
        evidence.append(polres_evidence)

    if contains_word(t, "jawa timur") or contains_word(t, "jatim") or contains_word(t, "polda jatim"):
        scores.append(90)
        evidence.append("Jawa Timur/Jatim")

    # Exact city/kabupaten names in the title are valid Jatim evidence,
    # but do NOT infer a Polres from a bare locality.
    for location in JATIM_LOCATIONS:
        if contains_word(t, location):
            scores.append(70)
            evidence.append(location)

    if scores:
        return {
            "is_jatim": True,
            "region": "Jawa Timur",
            "area_label": polres or "Jawa Timur",
            "locality": locality_from_polres(polres) or next((
                loc.title() for loc in JATIM_LOCATIONS if contains_word(t, loc)
            ), ""),
            "polres": polres,
            "confidence": max(scores),
            "evidence": sorted(set(evidence)),
            "source": "title",
        }

    # Anything without a canonical Jatim title signal is explicitly
    # labeled LUAR JATIM. This does not mean the incident is "unimportant".
    return {
        "is_jatim": False,
        "region": "LUAR JATIM",
        "area_label": "LUAR JATIM",
        "locality": "",
        "polres": None,
        "confidence": 0,
        "evidence": [],
        "source": "title",
    }
