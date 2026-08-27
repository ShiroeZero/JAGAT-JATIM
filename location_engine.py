import re

# ============================================================
# MASTER: 39 POLRES / SATWIL JAWA TIMUR
# ============================================================
# Important: a city/area name is NOT automatically a Polres.
# A Polres is assigned only when the article title explicitly
# names the institution/satker (or an unambiguous official alias).

POLRES_MAP = {
    "POLRES PELABUHAN TANJUNG PERAK": [
        "polres pelabuhan tanjung perak",
        "polres tanjung perak",
        "kepolisian resor pelabuhan tanjung perak",
    ],
    "POLRES JEMBER": ["polres jember", "kepolisian resor jember"],
    "POLRES KEDIRI": ["polres kediri", "kepolisian resor kediri"],
    "POLRES BLITAR KOTA": ["polres blitar kota", "polresta blitar", "kepolisian resor blitar kota", "kepolisian resor kota blitar"],
    "POLRESTABES SURABAYA": ["polrestabes surabaya", "polres kota besar surabaya", "kepolisian resor kota besar surabaya"],
    "POLRESTA MALANG KOTA": ["polresta malang kota", "polresta malang", "polres malang kota", "kepolisian resor kota malang", "kepolisian resor malang kota"],
    "POLRESTA SIDOARJO": ["polresta sidoarjo", "polres sidoarjo", "kepolisian resor kota sidoarjo", "kepolisian resor sidoarjo"],
    "POLRESTA BANYUWANGI": ["polresta banyuwangi", "polres banyuwangi", "kepolisian resor kota banyuwangi", "kepolisian resor banyuwangi"],
    "POLRESTA TUBAN": ["polresta tuban", "polres tuban", "kepolisian resor tuban", "kepolisian resor kota tuban"],
    "POLRESTA SUMENEP": ["polresta sumenep", "polres sumenep", "kepolisian resor sumenep"],
    "POLRES GRESIK": ["polres gresik", "kepolisian resor gresik"],
    "POLRES MALANG": ["polres malang", "kepolisian resor malang"],
    "POLRES PASURUAN": ["polres pasuruan", "kepolisian resor pasuruan"],
    "POLRES PASURUAN KOTA": ["polres pasuruan kota", "polresta pasuruan", "kepolisian resor kota pasuruan"],
    "POLRES PROBOLINGGO": ["polres probolinggo", "kepolisian resor probolinggo"],
    "POLRES PROBOLINGGO KOTA": ["polres probolinggo kota", "polresta probolinggo", "kepolisian resor kota probolinggo"],
    "POLRES LUMAJANG": ["polres lumajang", "kepolisian resor lumajang"],
    "POLRES BATU": ["polres batu", "polresta batu", "kepolisian resor batu"],
    "POLRES BONDOWOSO": ["polres bondowoso", "kepolisian resor bondowoso"],
    "POLRES SITUBONDO": ["polres situbondo", "kepolisian resor situbondo"],
    "POLRES KEDIRI KOTA": ["polres kediri kota", "polresta kediri", "kepolisian resor kediri kota", "kepolisian resor kota kediri"],
    "POLRES TULUNGAGUNG": ["polres tulungagung", "kepolisian resor tulungagung"],
    "POLRES NGANJUK": ["polres nganjuk", "kepolisian resor nganjuk"],
    "POLRES TRENGGALEK": ["polres trenggalek", "kepolisian resor trenggalek"],
    "POLRES BLITAR": ["polres blitar", "kepolisian resor blitar"],
    "POLRES MADIUN": ["polres madiun", "kepolisian resor madiun"],
    "POLRES MADIUN KOTA": ["polres madiun kota", "polresta madiun", "kepolisian resor kota madiun", "kepolisian resor madiun kota"],
    "POLRES NGAWI": ["polres ngawi", "kepolisian resor ngawi"],
    "POLRES MAGETAN": ["polres magetan", "kepolisian resor magetan"],
    "POLRES PONOROGO": ["polres ponorogo", "kepolisian resor ponorogo"],
    "POLRES PACITAN": ["polres pacitan", "kepolisian resor pacitan"],
    "POLRES BOJONEGORO": ["polres bojonegoro", "kepolisian resor bojonegoro"],
    "POLRES LAMONGAN": ["polres lamongan", "kepolisian resor lamongan"],
    "POLRES MOJOKERTO": ["polres mojokerto", "kepolisian resor mojokerto"],
    "POLRES MOJOKERTO KOTA": ["polres mojokerto kota", "polresta mojokerto", "kepolisian resor kota mojokerto", "kepolisian resor mojokerto kota"],
    "POLRES JOMBANG": ["polres jombang", "kepolisian resor jombang"],
    "POLRES PAMEKASAN": ["polres pamekasan", "kepolisian resor pamekasan"],
    "POLRES BANGKALAN": ["polres bangkalan", "kepolisian resor bangkalan"],
    "POLRES SAMPANG": ["polres sampang", "kepolisian resor sampang"],
}

JATIM_LOCATIONS = [
    "surabaya", "sidoarjo", "gresik", "lamongan", "tuban", "bojonegoro",
    "ngawi", "magetan", "madiun", "ponorogo", "pacitan", "nganjuk", "kediri",
    "tulungagung", "trenggalek", "blitar", "malang", "batu", "pasuruan",
    "probolinggo", "lumajang", "jember", "bondowoso", "situbondo", "banyuwangi",
    "mojokerto", "jombang", "pamekasan", "bangkalan", "sampang", "sumenep", "madura",
]

# Known non-Jatim compounds that would otherwise create false matches
# because they contain a Jatim locality token (e.g. Batu Bara -> Batu).
OUTSIDE_COMPOUNDS = [
    "batu bara",
    "polres batu bara",
    "kepolisian resor batu bara",
]

POLRES_TO_LOCALITY = {}
for polres in POLRES_MAP:
    low = polres.lower()
    locality = ""
    for key in ["surabaya", "sidoarjo", "gresik", "lamongan", "tuban", "bojonegoro", "ngawi", "magetan", "madiun", "ponorogo", "pacitan", "nganjuk", "tulungagung", "trenggalek", "blitar", "malang", "batu", "pasuruan", "probolinggo", "lumajang", "jember", "bondowoso", "situbondo", "banyuwangi", "mojokerto", "jombang", "pamekasan", "bangkalan", "sampang", "sumenep"]:
        if key in low:
            locality = key.title()
            break
    if polres == "POLRES PELABUHAN TANJUNG PERAK":
        locality = "Surabaya"
    POLRES_TO_LOCALITY[polres] = locality


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_word(text, term):
    text = normalize(text)
    term = normalize(term)
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def strip_publisher_suffix(title, source=""):
    title = str(title or "").strip()
    source = str(source or "").strip()
    if source:
        title = re.sub(r"\s+(?:-|–|—|\|)\s*" + re.escape(source) + r"\s*$", "", title, flags=re.IGNORECASE)
    return title.strip()


def _outside_compound_hit(text):
    return any(contains_word(text, phrase) for phrase in OUTSIDE_COMPOUNDS)


def detect_polres(title):
    """Return Polres only from an explicit institution/satker phrase."""
    t = normalize(title)
    if _outside_compound_hit(t):
        return None, None
    matches = []
    for polres, aliases in POLRES_MAP.items():
        for alias in aliases:
            if contains_word(t, alias):
                matches.append((len(alias), polres, alias))
    if not matches:
        return None, None
    matches.sort(key=lambda x: x[0], reverse=True)
    _, polres, evidence = matches[0]
    return polres, evidence


def locality_from_polres(polres):
    return POLRES_TO_LOCALITY.get(str(polres or ""), "")


def detect_locality(title):
    t = normalize(title)
    if _outside_compound_hit(t):
        return ""
    matches = [loc for loc in JATIM_LOCATIONS if contains_word(t, loc)]
    if not matches:
        return ""
    matches.sort(key=len, reverse=True)
    return matches[0].title()


def detect_location(title, description="", source=""):
    """
    Canonical geography from ARTICLE TITLE ONLY.

    Hierarchy:
      region -> Jawa Timur / LUAR JATIM
      locality -> district/city when stated in title
      polres -> only when institution is explicitly named

    Publisher/source/description are never geographic evidence.
    """
    title = strip_publisher_suffix(title, source)
    t = normalize(title)

    if _outside_compound_hit(t):
        return {
            "is_jatim": False,
            "region": "LUAR JATIM",
            "locality": "",
            "area_label": "LUAR JATIM",
            "polres": None,
            "confidence": 100,
            "evidence": [c for c in OUTSIDE_COMPOUNDS if contains_word(t, c)],
            "source": "title",
        }

    polres, polres_evidence = detect_polres(t)
    locality = locality_from_polres(polres) if polres else detect_locality(t)
    explicit_jatim = (
        contains_word(t, "jawa timur")
        or contains_word(t, "jatim")
        or contains_word(t, "polda jatim")
        or contains_word(t, "polda jawa timur")
    )

    if polres or locality or explicit_jatim:
        evidence = []
        if polres_evidence:
            evidence.append(polres_evidence)
        if locality:
            evidence.append(locality)
        if explicit_jatim:
            evidence.append("Jawa Timur/Jatim")
        return {
            "is_jatim": True,
            "region": "Jawa Timur",
            "locality": locality,
            "area_label": locality or "Jawa Timur (Umum)",
            "polres": polres,
            "confidence": 100 if polres else (95 if locality else 90),
            "evidence": sorted(set(evidence)),
            "source": "title",
        }

    return {
        "is_jatim": False,
        "region": "LUAR JATIM",
        "locality": "",
        "area_label": "LUAR JATIM",
        "polres": None,
        "confidence": 0,
        "evidence": [],
        "source": "title",
    }
