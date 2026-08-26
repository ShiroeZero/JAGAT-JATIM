import datetime as dt
import hashlib
import html
import json
import os
import re
import time
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


OUT = "data/news.json"
USER_AGENT = "JAGAT-News-Monitor/6.1"
DISCOVERY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "discovery_patterns_v6.json")


def load_discovery_config():
    try:
        with open(DISCOVERY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"WARN: discovery patterns tidak dapat dimuat: {exc}")
        return {"families": {}}


DISCOVERY_CONFIG = load_discovery_config()
DISCOVERY_FAMILIES = DISCOVERY_CONFIG.get("families", {})
DISCOVERY_TERMS = []
for _family in DISCOVERY_FAMILIES.values():
    DISCOVERY_TERMS.extend(_family.get("terms", []))
DISCOVERY_TERMS = sorted(set(DISCOVERY_TERMS), key=lambda x: (len(x), x), reverse=True)


# ============================================================
# GENERAL SEARCH QUERIES
# ============================================================

GENERAL_QUERIES = [
    '"oknum polisi" Indonesia',
    '"oknum Polri" Indonesia',
    '"anggota polisi" ditangkap',
    '"anggota Polri" ditangkap',
    '"anggota polisi" tersangka',
    '"anggota Polri" tersangka',
    '"polisi" "ditetapkan sebagai tersangka"',
    '"polisi" "menjadi tersangka"',
    '"polisi" "terlibat" kasus',
    '"polisi" diduga',
    '"polisi" ditahan',
    '"polisi" diperiksa Propam',
    '"polisi" pelanggaran etik',
    '"polisi" pelanggaran disiplin',
    '"polisi" dipecat',
    '"polisi" diberhentikan',
    '"polisi" narkoba',
    '"polisi" korupsi',
    '"polisi" pungli',
    '"polisi" pemerasan',
    '"polisi" penganiayaan',
    '"polisi" penembakan',
    '"polisi" kekerasan',
    '"polisi" suap',
    '"polisi" penyalahgunaan wewenang',
    '"polisi" ungkap kasus',
    '"polisi" tangkap pelaku',
    '"polisi" amankan tersangka',
    '"polisi" Jawa Timur',
    '"oknum polisi" Jawa Timur',
]


# ============================================================
# 39 POLRES JAWA TIMUR
#
# Alias pertama = indikator institusi/satker yang kuat.
# Nama kota/kabupaten TIDAK otomatis menjadi Polres.
# ============================================================

POLRES = {
    "POLRES PELABUHAN TANJUNG PERAK": [
        "polres pelabuhan tanjung perak",
        "polres tanjung perak",
        "kepolisian resor pelabuhan tanjung perak",
    ],

    "POLRES JEMBER": [
        "polres jember",
        "kepolisian resor jember",
        "polres kabupaten jember",
    ],

    "POLRES KEDIRI KOTA": [
        "polres kediri kota",
        "polresta kediri",
        "kepolisian resor kediri kota",
        "kepolisian resor kota kediri",
    ],

    "POLRES KEDIRI": [
        "polres kediri",
        "kepolisian resor kediri",
    ],

    "POLRES BLITAR KOTA": [
        "polres blitar kota",
        "polresta blitar",
        "kepolisian resor blitar kota",
        "kepolisian resor kota blitar",
    ],

    "POLRES BLITAR": [
        "polres blitar",
        "kepolisian resor blitar",
    ],

    "POLRESTABES SURABAYA": [
        "polrestabes surabaya",
        "polres kota besar surabaya",
        "kepolisian resor kota besar surabaya",
    ],

    "POLRESTA MALANG KOTA": [
        "polresta malang kota",
        "polresta malang",
        "polres malang kota",
        "kepolisian resor kota malang",
        "kepolisian resor malang kota",
    ],

    "POLRESTA SIDOARJO": [
        "polresta sidoarjo",
        "polres sidoarjo",
        "kepolisian resor kota sidoarjo",
        "kepolisian resor sidoarjo",
    ],

    "POLRESTA BANYUWANGI": [
        "polresta banyuwangi",
        "polres banyuwangi",
        "kepolisian resor kota banyuwangi",
        "kepolisian resor banyuwangi",
    ],

    "POLRESTA TUBAN": [
        "polresta tuban",
        "polres tuban",
        "kepolisian resor tuban",
        "kepolisian resor kota tuban",
    ],

    "POLRESTA SUMENEP": [
        "polresta sumenep",
        "polres sumenep",
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

    "POLRES PASURUAN KOTA": [
        "polres pasuruan kota",
        "polresta pasuruan",
        "kepolisian resor kota pasuruan",
        "kepolisian resor pasuruan kota",
    ],

    "POLRES PASURUAN": [
        "polres pasuruan",
        "kepolisian resor pasuruan",
    ],

    "POLRES PROBOLINGGO KOTA": [
        "polres probolinggo kota",
        "polresta probolinggo",
        "kepolisian resor kota probolinggo",
        "kepolisian resor probolinggo kota",
    ],

    "POLRES PROBOLINGGO": [
        "polres probolinggo",
        "kepolisian resor probolinggo",
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

    "POLRES MADIUN KOTA": [
        "polres madiun kota",
        "polresta madiun",
        "kepolisian resor kota madiun",
        "kepolisian resor madiun kota",
    ],

    "POLRES MADIUN": [
        "polres madiun",
        "kepolisian resor madiun",
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

    "POLRES MOJOKERTO KOTA": [
        "polres mojokerto kota",
        "polresta mojokerto",
        "kepolisian resor kota mojokerto",
        "kepolisian resor mojokerto kota",
    ],

    "POLRES MOJOKERTO": [
        "polres mojokerto",
        "kepolisian resor mojokerto",
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


# ============================================================
# WILAYAH JAWA TIMUR
# ============================================================

JATIM_REGION_TERMS = [
    "jawa timur",
    "jatim",
    "polda jatim",
    "polda jawa timur",
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
    "trenggalek",
    "blitar",
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
    "sampang",
    "bangkalan",
    "sumenep",
]


# ============================================================
# NON-JATIM
# ============================================================

NON_JATIM_TERMS = [
    "riau",
    "pekanbaru",
    "dumai",
    "bengkalis",
    "siak",
    "kampar",
    "pelalawan",
    "indragiri",
    "kuantan singingi",
    "rokan hilir",
    "rokan hulu",
    "meranti",
    "kepulauan riau",
    "batam",
    "tanjungpinang",
    "jambi",
    "sumatera barat",
    "sumatera utara",
    "sumatera selatan",
    "lampung",
    "bengkulu",
    "kalimantan",
    "sulawesi",
    "papua",
    "maluku",
    "bali",
    "ntb",
    "ntt",
    "jawa tengah",
    "jateng",
    "jawa barat",
    "jabar",
    "banten",
    "dki jakarta",
    "jakarta",
]


# ============================================================
# NEGATIVE / OKNUM
# ============================================================

NEGATIVE_OKNUM_TERMS = [
    "oknum polisi",
    "oknum polri",
    "anggota polisi ditangkap",
    "anggota polri ditangkap",
    "anggota polisi tersangka",
    "anggota polri tersangka",
    "polisi ditetapkan sebagai tersangka",
    "polisi menjadi tersangka",
    "polisi terlibat",
    "polisi diduga",
    "polisi ditahan",
    "polisi diperiksa",
    "polisi dipecat",
    "polisi diberhentikan",
    "polisi melakukan penganiayaan",
    "polisi melakukan kekerasan",
    "polisi menembak",
    "polisi terlibat narkoba",
    "polisi konsumsi narkoba",
    "polisi positif narkoba",
    "polisi korupsi",
    "polisi menerima suap",
    "polisi menerima uang",
    "polisi pungli",
    "polisi memeras",
    "polisi melakukan pemerasan",
    "polisi menyalahgunakan wewenang",
    "pelanggaran etik polisi",
    "pelanggaran disiplin polisi",
    "anggota polisi melakukan",
]


ETHIC_TERMS = [
    "kode etik",
    "pelanggaran etik",
    "pelanggaran disiplin",
    "disiplin polisi",
    "etik polisi",
    "propam",
    "dipecat",
    "ptdh",
    "pemberhentian",
]


ABUSE_TERMS = [
    "penyalahgunaan wewenang",
    "menyalahgunakan wewenang",
    "salahgunakan wewenang",
    "pungli",
    "memeras",
    "pemerasan",
    "suap",
    "gratifikasi",
]


CRIME_TERMS = [
    "narkoba",
    "sabu",
    "ganja",
    "ekstasi",
    "narkotika",
    "korupsi",
    "suap",
    "gratifikasi",
    "pungli",
    "pemerasan",
    "penganiayaan",
    "kekerasan",
    "penembakan",
    "menembak",
    "pemukulan",
    "pengeroyokan",
]


# ============================================================
# UNGKAP KASUS
# ============================================================

CASE_TERMS = [
    "ungkap kasus",
    "mengungkap kasus",
    "pengungkapan kasus",
    "mengungkap",
    "tangkap pelaku",
    "menangkap pelaku",
    "amankan tersangka",
    "mengamankan tersangka",
    "berhasil menangkap",
    "berhasil mengamankan",
    "gelar perkara",
    "sita",
    "menyita",
    "gagalkan",
    "menggagalkan",
    "razia",
    "operasi",
    "penindakan",
    "ringkus pelaku",
    "meringkus pelaku",
]


# ============================================================
# POSITIVE
# ============================================================

POSITIVE_TERMS = [
    "prestasi",
    "penghargaan",
    "apresiasi",
    "pelayanan",
    "bakti sosial",
    "pengamanan",
    "patroli",
    "imbauan",
    "sosialisasi",
    "inovasi pelayanan",
]


# ============================================================
# NEGATIVE KINERJA
# ============================================================

SERVICE_NEGATIVE_TERMS = [
    "pelayanan buruk",
    "keluhan polisi",
    "protes terhadap polisi",
    "polisi dilaporkan",
    "polisi diduga lalai",
    "kelalaian polisi",
    "kritik polisi",
    "pelayanan polisi dikeluhkan",
]


# ============================================================
# UTILITY
# ============================================================

def clean(value):
    return re.sub(
        r"\s+",
        " ",
        html.unescape(value or "")
    ).strip()


def strip_html(value):
    return clean(
        re.sub(
            r"<[^>]+>",
            " ",
            value or ""
        )
    )


def contains_term(text, term):
    text = text.lower()
    term = term.lower().strip()

    if " " in term:
        return term in text

    return re.search(
        r"(?<![a-z])"
        + re.escape(term)
        + r"(?![a-z])",
        text
    ) is not None


def parse_date(value):
    try:
        return parsedate_to_datetime(
            value
        ).astimezone(
            dt.timezone.utc
        )
    except Exception:
        return None


def iso_or_none(value):
    parsed = parse_date(value)

    if parsed is None:
        return None

    return parsed.isoformat()


def get(url):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    with urlopen(
        request,
        timeout=20
    ) as response:

        return response.read()


# ============================================================
# POLRES DETECTION
# ============================================================

def find_polres(text):

    candidates = []

    for polres_name, aliases in POLRES.items():

        for alias in aliases:

            if contains_term(
                text,
                alias
            ):

                candidates.append(
                    (
                        len(alias),
                        polres_name
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# REGION DETECTION
# ============================================================

def detect_region(text, polres):

    if polres:
        return True

    jatim_hits = [
        term
        for term in JATIM_REGION_TERMS
        if contains_term(
            text,
            term
        )
    ]

    non_jatim_hits = [
        term
        for term in NON_JATIM_TERMS
        if contains_term(
            text,
            term
        )
    ]

    if non_jatim_hits:
        return False

    return bool(jatim_hits)


# ============================================================
# DISCOVERY / ATTENTION SIGNALS
# ============================================================

POLICE_ANCHORS = [
    "polisi", "polri", "polda", "polres", "polresta", "polrestabes",
    "polsek", "propam", "paminal", "provost", "brimob", "satres",
    "satlantas", "reskrim", "resnarkoba", "jatanras", "mako",
    "pos polisi", "anggota", "oknum"
]


def has_any_term(text, terms):
    return any(contains_term(text, term) for term in terms)


def discovery_matches(text):
    text = clean(text).lower()
    families = []
    tags = set()
    matched_terms = []
    for key, family in DISCOVERY_FAMILIES.items():
        hits = [term for term in family.get("terms", []) if contains_term(text, term)]
        if hits:
            families.append(key)
            matched_terms.extend(hits[:6])
            tags.update(family.get("tags", []))
    return sorted(set(families)), sorted(tags), sorted(set(matched_terms), key=len, reverse=True)[:20]


# ============================================================
# ARTICLE CLASSIFICATION
# ============================================================

def classify_article(
    title,
    description
):

    text = clean(title + " " + strip_html(description)).lower()
    polres = find_polres(clean(title).lower())
    is_jatim = detect_region(clean(title).lower(), polres)
    discovery_families, discovery_tags, discovery_hits = discovery_matches(text)
    police_context = has_any_term(text, POLICE_ANCHORS)

    is_negative_oknum = any(contains_term(text, term) for term in NEGATIVE_OKNUM_TERMS)
    misconduct_families = {
        "case_handling", "financial_misconduct", "abuse_of_power",
        "ethics_personal_misconduct", "illegal_activity_backing",
        "journalist_and_information", "service_corruption",
        "general_police_misconduct"
    }
    if police_context and misconduct_families.intersection(discovery_families):
        is_negative_oknum = True

    security_direct = "security_public_order" in discovery_families and police_context
    family_category = {
        "case_handling": "OKNUM - PENANGANAN PERKARA",
        "financial_misconduct": "OKNUM - INTEGRITAS/KEUANGAN",
        "abuse_of_power": "OKNUM - PENYALAHGUNAAN WEWENANG",
        "ethics_personal_misconduct": "OKNUM - ETIK/PERSONAL",
        "illegal_activity_backing": "AKTIVITAS ILEGAL / DUGAAN PEMBIARAN",
        "journalist_and_information": "OKNUM - HUBUNGAN DENGAN PERS",
        "service_corruption": "OKNUM - LAYANAN/SATPAS/SAMSAT",
        "general_police_misconduct": "OKNUM - ETIK/DISIPLIN",
        "security_public_order": "KEAMANAN / KAMTIBMAS",
    }
    family_precedence = [
        "security_public_order",
        "journalist_and_information",
        "financial_misconduct",
        "abuse_of_power",
        "ethics_personal_misconduct",
        "service_corruption",
        "illegal_activity_backing",
        "case_handling",
        "general_police_misconduct",
    ]
    matched_family = next((name for name in family_precedence if name in discovery_families), None)

    if is_negative_oknum or security_direct:
        category = family_category.get(matched_family, "OKNUM - PIDANA")
        scope = "negative"
        scope_label = "NEGATIF / ATENSI"
    elif any(contains_term(text, term) for term in SERVICE_NEGATIVE_TERMS):
        category = "KINERJA/LAYANAN POLRI"
        scope = "negative"
        scope_label = "NEGATIF / KINERJA"
    elif any(contains_term(text, term) for term in CASE_TERMS):
        category = "UNGKAP KASUS / PENINDAKAN"
        scope = "case"
        scope_label = "UNGKAP KASUS"
    elif any(contains_term(text, term) for term in POSITIVE_TERMS):
        category = "PRESTASI / KEGIATAN POSITIF"
        scope = "positive"
        scope_label = "POSITIF / KEGIATAN"
    else:
        category = "NETRAL / LAINNYA"
        scope = "neutral"
        scope_label = "NETRAL"

    negative_hits = sum(1 for term in NEGATIVE_OKNUM_TERMS if contains_term(text, term))
    crime_hits = sum(1 for term in CRIME_TERMS if contains_term(text, term))
    ethic_hits = sum(1 for term in ETHIC_TERMS if contains_term(text, term))
    score = negative_hits * 2 + crime_hits + ethic_hits + len(discovery_families)

    if is_negative_oknum and score >= 4:
        priority = "high"
    elif is_negative_oknum or security_direct or score >= 2:
        priority = "medium"
    else:
        priority = "low"

    return (
        is_jatim, polres, category, scope, scope_label, priority,
        discovery_families, discovery_tags, discovery_hits,
    )


# ============================================================
# QUERY BUILDER
# ============================================================

def priority_weight(value):
    return {"high": 3, "medium": 2, "low": 1}.get(str(value or "low").lower(), 1)


def parse_dt(value):
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except Exception:
        return None


def load_case_followup_queries():
    case_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "case_clusters.json")
    try:
        with open(case_file, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    cases = data.get("cases", []) if isinstance(data, dict) else []
    now = dt.datetime.now(dt.timezone.utc)
    selected = []
    generic = {"kasus", "polisi", "polri", "anggota", "oknum", "viral", "diduga", "misteri", "hati", "foto", "warga", "orang", "pelaku", "motor"}
    followup_anchors = {term.lower() for term in DISCOVERY_TERMS} | {
        "narkoba", "sabu", "narkotika", "pencurian", "pengeroyokan", "penganiayaan",
        "kekerasan", "pembunuhan", "penipuan", "judi", "judol", "rokok ilegal",
        "tambang", "aborsi", "perselingkuhan", "wartawan", "jurnalis", "intimidasi"
    }

    for case in cases:
        priority = str(case.get("priority", "low")).lower()
        article_count = int(case.get("article_count", 0) or 0)
        if not bool(case.get("is_jatim", False)):
            continue
        if priority not in {"high", "medium"} and article_count < 3:
            continue
        last = parse_dt(case.get("last_detected_at") or case.get("last_seen"))
        if last is None or (now - last).days > 14:
            continue

        event_terms = [
            str(x).strip().lower()
            for x in (case.get("event_terms") or case.get("incident_terms") or [])
            if len(str(x).strip()) >= 4 and str(x).strip().lower() not in generic
        ]
        usable = [term for term in event_terms if term in followup_anchors][:2]
        if not usable:
            continue

        polres = str(case.get("polres") or "").strip()
        region = str(case.get("region") or "").strip()
        locality = polres or region
        if locality and locality.lower() not in {"indonesia", "jawa timur"}:
            query = f'"{locality}" "{" ".join(usable)}"'
        else:
            query = f'polisi "{" ".join(usable)}"'
        selected.append((priority_weight(priority), article_count, last, query))

    selected.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return [q for _, _, _, q in selected[:8]]


def build_queries():
    """
    Jatim-focused discovery matrix.

    The system is not intended to monitor every Indonesian province.
    Broad national queries are retained as a safety net, while the main
    discovery effort is concentrated on Jawa Timur and the 39 Polres.
    """
    queries = list(GENERAL_QUERIES)

    # Curated high-value variants learned from the supplied 2026 headline corpus.
    curated_terms = [
        "tangkap lepas", "tebusan", "setoran", "upeti", "pungli",
        "pungutan liar", "suap", "gratifikasi", "pemerasan", "minta uang",
        "penyalahgunaan wewenang", "ketidakprofesionalan", "maladministrasi",
        "intervensi", "salah tangkap", "kriminalisasi", "intimidasi wartawan",
        "halangi peliputan", "perselingkuhan", "nikah siri", "pencabulan",
        "pemerkosaan", "kekerasan seksual", "aborsi", "kdrt",
        "tambang ilegal", "galian c ilegal", "sabung ayam", "judi online",
        "rokok ilegal", "solar subsidi", "dibeking", "pembiaran",
        "calo sim", "jalur belakang sim", "pungli samsat", "jual beli stck",
        "pelanggaran etik", "sidang etik", "propam periksa", "demo ricuh",
        "bentrok", "tawuran", "mako diserang", "pos polisi dibakar",
        "polisi dibacok",
    ]
    for term in curated_terms:
        queries.append(f'"polisi" "Jawa Timur" "{term}"')

    # Polda Jatim / Propam discovery.
    for term in [
        "oknum", "Propam", "pungli", "setoran", "suap", "pemerasan",
        "tangkap lepas", "intimidasi wartawan", "tambang ilegal", "judi",
        "narkoba", "aborsi", "perselingkuhan", "kekerasan", "demo ricuh",
    ]:
        queries.append(f'"Polda Jatim" "{term}"')
        queries.append(f'"Polda Jawa Timur" "{term}"')

    # Every Polres is covered, but only with a small number of high-recall queries.
    for polres_name, aliases in POLRES.items():
        anchor = aliases[0]
        queries.append(f'"{anchor}"')
        queries.append(f'"{anchor}" "Propam"')
        queries.append(f'"{anchor}" "pungli"')

    # Active case follow-up is the highest-value historical query layer.
    queries.extend(load_case_followup_queries())

    result = []
    seen = set()
    for query in queries:
        key = query.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(query)

    return result


# ============================================================
# CURSOR / INCREMENTAL
# ============================================================

def get_last_successful_fetch(old):

    value = old.get(
        "last_successful_fetch"
    )

    if value:
        try:
            return dt.datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            ).astimezone(
                dt.timezone.utc
            )
        except Exception:
            pass

    # --------------------------------------------------------
    # MIGRATION:
    #
    # File lama belum mempunyai cursor.
    #
    # Gunakan artikel TERBARU sebagai cursor awal.
    # Jadi seluruh database lama TIDAK diambil ulang.
    #
    # Kita mundurkan 5 menit sebagai overlap kecil untuk
    # menghindari artikel dengan timestamp yang sama.
    # Dedup akan membuang artikel lama.
    # --------------------------------------------------------

    existing_dates = []

    for item in old.get(
        "items",
        []
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        value = item.get(
            "published_at"
        )

        if not value:
            continue

        try:

            parsed = dt.datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=dt.timezone.utc
                )

            existing_dates.append(
                parsed.astimezone(
                    dt.timezone.utc
                )
            )

        except Exception:
            continue

    if existing_dates:

        latest_existing = max(
            existing_dates
        )

        return (
            latest_existing
            - dt.timedelta(
                minutes=5
            )
        )

    # --------------------------------------------------------
    # Benar-benar database kosong.
    # --------------------------------------------------------

    return (
        dt.datetime.now(
            dt.timezone.utc
        )
        - dt.timedelta(
            days=2
        )
    )


# ============================================================
# ARTICLE IS NEW ENOUGH?
# ============================================================

def is_after_cursor(
    published_at,
    cursor
):

    if published_at is None:
        return True

    if published_at.tzinfo is None:

        published_at = published_at.replace(
            tzinfo=dt.timezone.utc
        )

    return (
        published_at.astimezone(
            dt.timezone.utc
        )
        >= cursor
    )


# ============================================================
# MAIN
# ============================================================

def main():

    now = dt.datetime.now(
        dt.timezone.utc
    )

    old = {
        "items": []
    }

    # --------------------------------------------------------
    # LOAD EXISTING DATA
    # --------------------------------------------------------

    if os.path.exists(
        OUT
    ):

        try:

            with open(
                OUT,
                "r",
                encoding="utf-8"
            ) as file:

                old = json.load(
                    file
                )

        except Exception as exc:

            raise RuntimeError(
                "Gagal membaca "
                + OUT
                + ": "
                + str(exc)
            )

    items = old.get(
        "items",
        []
    )

    if not isinstance(
        items,
        list
    ):

        items = []

    # --------------------------------------------------------
    # EXISTING INDEX
    #
    # ID / URL dipakai untuk dedup.
    # --------------------------------------------------------

    seen = set()

    for item in items:

        if not isinstance(
            item,
            dict
        ):
            continue

        identity = (
            item.get("id")
            or item.get("url")
        )

        if identity:
            seen.add(
                identity
            )

    # --------------------------------------------------------
    # CURSOR
    # --------------------------------------------------------

    cursor = get_last_successful_fetch(
        old
    )

    cursor_text = cursor.isoformat()

    print(
        "=========================================="
    )

    print(
        "PNM — NEWS MONITOR"
    )

    print(
        "INCREMENTAL FETCH V6 — DISCOVERY MATRIX"
    )

    print(
        "=========================================="
    )

    print(
        f"Existing records : {len(items)}"
    )

    print(
        f"Last successful  : {cursor_text}"
    )

    print(
        "Mode             : INCREMENTAL"
    )

    print(
        "=========================================="
    )

    queries = build_queries()

    added = 0
    skipped_old = 0
    skipped_duplicate = 0
    skipped_irrelevant = 0
    api_success = 0
    api_failed = 0

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Kita TIDAK melakukan:
    #
    #   Reclassifying 5000 existing records
    #
    # Existing records dipertahankan apa adanya.
    # Hanya artikel baru yang diproses.
    # --------------------------------------------------------

    for index, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"[{index}/{len(queries)}] "
            f"{query}"
        )

        try:

            url = (
                "https://news.google.com/rss/search?q="
                + quote(query)
                + "&hl=id&gl=ID&ceid=ID:id"
            )

            rss_data = get(
                url
            )

            root = ET.fromstring(
                rss_data
            )

            api_success += 1

            for article in root.findall(
                "./channel/item"
            ):

                title = clean(
                    article.findtext(
                        "title"
                    )
                )

                link = clean(
                    article.findtext(
                        "link"
                    )
                )

                description = clean(
                    article.findtext(
                        "description"
                    )
                )

                if not title or not link:
                    continue

                published_raw = (
                    article.findtext(
                        "pubDate"
                    )
                )

                published_dt = parse_date(
                    published_raw
                )

                # ------------------------------------------------
                # TIMESTAMP FILTER
                #
                # Artikel lama tidak diproses.
                # ------------------------------------------------

                if not is_after_cursor(
                    published_dt,
                    cursor
                ):

                    skipped_old += 1
                    continue

                # ------------------------------------------------
                # ID
                # ------------------------------------------------

                identity = hashlib.sha1(
                    (
                        title
                        + "|"
                        + link
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()

                # ------------------------------------------------
                # DUPLICATE
                # ------------------------------------------------

                if identity in seen:

                    skipped_duplicate += 1
                    continue

                # ------------------------------------------------
                # RELEVANCE
                # ------------------------------------------------

                searchable_text = (
                    title
                    + " "
                    + description
                ).lower()

                relevance_anchor = has_any_term(searchable_text, POLICE_ANCHORS)
                discovery_anchor = has_any_term(searchable_text, DISCOVERY_TERMS)
                regional_anchor = has_any_term(searchable_text, JATIM_REGION_TERMS)

                if not (relevance_anchor or (discovery_anchor and regional_anchor)):
                    skipped_irrelevant += 1
                    continue

                # ------------------------------------------------
                # SOURCE
                # ------------------------------------------------

                source = clean(
                    article.findtext(
                        "source"
                    )
                )

                if not source:
                    source = "Google News"

                # ------------------------------------------------
                # CLASSIFY NEW ARTICLE ONLY
                # ------------------------------------------------

                (
                    is_jatim,
                    polres,
                    category,
                    scope,
                    scope_label,
                    priority,
                    discovery_families,
                    discovery_tags,
                    discovery_hits,
                ) = classify_article(
                    title,
                    description
                )

                item = {

                    "id":
                        identity,

                    "title":
                        title,

                    "url":
                        link,

                    "source":
                        source,

                    "published_at":
                        (
                            published_dt.isoformat()
                            if published_dt
                            else now.isoformat()
                        ),

                    "collected_at":
                        now.isoformat(),

                    "region":
                        (
                            "Jawa Timur"
                            if is_jatim
                            else "LUAR JATIM"
                        ),

                    "area_label":
                        (
                            polres
                            if polres
                            else ("Jawa Timur" if is_jatim else "LUAR JATIM")
                        ),

                    "is_jatim":
                        is_jatim,

                    "polres":
                        polres,

                    "category":
                        category,

                    "scope":
                        scope,

                    "scope_label":
                        scope_label,

                    "priority":
                        priority,

                    "summary":
                        strip_html(
                            description
                        )[:700],

                    # --------------------------------------------
                    # PROCESSING STATE
                    # --------------------------------------------

                    "processing_status":
                        "new",

                    "classifier_version":
                        "news-v6",

                    "classified_at":
                        now.isoformat(),

                    "case_id":
                        None,

                    "discovery_families":
                        discovery_families,

                    "discovery_tags":
                        discovery_tags,

                    "discovery_hits":
                        discovery_hits,

                    "discovery_version":
                        "discovery-v6",
                }

                items.append(
                    item
                )

                seen.add(
                    identity
                )

                added += 1

        except Exception as exc:

            api_failed += 1

            print(
                f"WARN: query gagal: "
                f"{query} -> {exc}"
            )

        time.sleep(
            0.15
        )

    # ========================================================
    # SORT
    # ========================================================

    items.sort(
        key=lambda item:
            item.get(
                "published_at",
                ""
            ),
        reverse=True
    )

    # ========================================================
    # LIMIT
    # ========================================================

    items = items[:5000]

    # ========================================================
    # SAFETY:
    #
    # last_successful_fetch hanya boleh maju jika SEMUA query
    # berhasil.
    #
    # Kalau ada query gagal:
    # cursor tetap menggunakan cursor lama.
    #
    # Tujuannya supaya berita tidak hilang pada workflow
    # berikutnya.
    # ========================================================

    all_queries_success = (
        api_failed == 0
    )

    if all_queries_success:

        new_last_successful_fetch = (
            now.isoformat()
        )

    else:

        old_cursor = old.get(
            "last_successful_fetch"
        )

        if old_cursor:

            new_last_successful_fetch = (
                old_cursor
            )

        else:

            new_last_successful_fetch = (
                cursor.isoformat()
            )

    # ========================================================
    # STATISTICS
    # ========================================================

    statistics = {

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

        "case":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "case"
            ),

        "positive":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "positive"
            ),

        "neutral":
            sum(
                1
                for item in items
                if item.get(
                    "scope"
                ) == "neutral"
            ),
    }

    # ========================================================
    # SAVE
    # ========================================================

    output = {

        "generated_at":
            now.isoformat(),

        "platform":
            "News",

        "total":
            len(items),

        "new_records":
            added,

        "last_successful_fetch":
            new_last_successful_fetch,

        "last_fetch_mode":
            "incremental",

        "fetch_status":
            (
                "success"
                if all_queries_success
                else "partial"
            ),

        "fetch_statistics": {

            "queries":
                len(queries),

            "api_success":
                api_success,

            "api_failed":
                api_failed,

            "skipped_old":
                skipped_old,

            "skipped_duplicate":
                skipped_duplicate,

            "skipped_irrelevant":
                skipped_irrelevant,

            "new_records":
                added,

            "discovery_version":
                "discovery-v6.1",

            "discovery_families":
                len(DISCOVERY_FAMILIES),

            "jatim_polres_count":
                len(POLRES),
        },

        "statistics":
            statistics,

        "items":
            items,
    }

    os.makedirs(
        os.path.dirname(OUT),
        exist_ok=True
    )

    with open(
        OUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    # ========================================================
    # LOG
    # ========================================================

    print(
        "=========================================="
    )

    print(
        f"API success       : {api_success}"
    )

    print(
        f"API failed        : {api_failed}"
    )

    print(
        f"Skipped old       : {skipped_old}"
    )

    print(
        f"Skipped duplicate : {skipped_duplicate}"
    )

    print(
        f"Skipped irrelevant: {skipped_irrelevant}"
    )

    print(
        f"New records       : {added}"
    )

    print(
        f"Total records     : {len(items)}"
    )

    print(
        f"Jawa Timur        : "
        f"{statistics['jatim']}"
    )

    print(
        f"Negative          : "
        f"{statistics['negative']}"
    )

    print(
        f"Ungkap kasus      : "
        f"{statistics['case']}"
    )

    print(
        f"Positive          : "
        f"{statistics['positive']}"
    )

    print(
        f"Neutral           : "
        f"{statistics['neutral']}"
    )

    print(
        f"Last successful   : "
        f"{new_last_successful_fetch}"
    )

    print(
        f"Output            : {OUT}"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
