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
USER_AGENT = "PNM-Polri-Negative-News-Monitor/4.1"


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
# IMPORTANT:
# - Alias pertama = indikator institusi/satker yang kuat.
# - Nama kota/kabupaten TIDAK otomatis menjadi Polres.
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
#
# Digunakan untuk menentukan REGION.
# Tidak digunakan langsung untuk menentukan POLRES.
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
#
# Dipakai untuk mencegah false positive.
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
# POSITIF
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
        re.sub(r"<[^>]+>", " ", value or "")
    )


def contains_term(text, term):
    """
    Pencocokan aman.

    Untuk frasa:
        'polres jember'

    menggunakan pencarian frasa.

    Untuk satu kata:
        'jember'

    menggunakan word boundary.
    """

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
        ).isoformat()

    except Exception:
        return dt.datetime.now(
            dt.timezone.utc
        ).isoformat()


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
    """
    HANYA menggunakan indikator institusi/satker.

    Nama kota/kabupaten tidak digunakan sebagai penentu Polres.

    Alias paling panjang diperiksa terlebih dahulu agar:

        POLRES KEDIRI KOTA

    tidak salah ditangkap sebagai:

        POLRES KEDIRI
    """

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

    # Alias paling spesifik menang.
    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# REGION DETECTION
# ============================================================

def detect_region(text, polres):
    """
    Menentukan apakah artikel termasuk Jawa Timur.

    Prioritas:
    1. Nama Polres Jatim eksplisit
    2. Indikator Jatim
    3. Jika ada indikator luar Jatim kuat, jangan paksa Jatim
    """

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

    # Jika ada wilayah luar Jatim yang jelas
    # dan tidak ada bukti institusi Jatim,
    # jangan klasifikasikan sebagai Jatim.
    if non_jatim_hits:
        return False

    return bool(jatim_hits)


# ============================================================
# ARTICLE CLASSIFICATION
# ============================================================

def classify_article(
    title,
    description
):

    text = clean(
        (
            title
            + " "
            + strip_html(description)
        )
    ).lower()

    # --------------------------------------------------------
    # POLRES
    # --------------------------------------------------------

    polres = find_polres(
        text
    )

    # --------------------------------------------------------
    # REGION
    # --------------------------------------------------------

    is_jatim = detect_region(
        text,
        polres
    )

    # --------------------------------------------------------
    # NEGATIVE OKNUM
    # --------------------------------------------------------

    is_negative_oknum = any(
        contains_term(
            text,
            term
        )
        for term in NEGATIVE_OKNUM_TERMS
    )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    if is_negative_oknum:

        if any(
            contains_term(
                text,
                term
            )
            for term in ETHIC_TERMS
        ):

            category = (
                "OKNUM - ETIK/DISIPLIN"
            )

        elif any(
            contains_term(
                text,
                term
            )
            for term in ABUSE_TERMS
        ):

            category = (
                "OKNUM - PENYALAHGUNAAN WEWENANG"
            )

        else:

            category = (
                "OKNUM - PIDANA"
            )

        scope = "negative"
        scope_label = (
            "NEGATIF / OKNUM"
        )

    elif any(
        contains_term(
            text,
            term
        )
        for term in SERVICE_NEGATIVE_TERMS
    ):

        category = (
            "KINERJA/LAYANAN POLRI"
        )

        scope = "negative"
        scope_label = (
            "NEGATIF / KINERJA"
        )

    elif any(
        contains_term(
            text,
            term
        )
        for term in CASE_TERMS
    ):

        category = (
            "UNGKAP KASUS / PENINDAKAN"
        )

        scope = "case"
        scope_label = (
            "UNGKAP KASUS"
        )

    elif any(
        contains_term(
            text,
            term
        )
        for term in POSITIVE_TERMS
    ):

        category = (
            "PRESTASI / KEGIATAN POSITIF"
        )

        scope = "positive"
        scope_label = (
            "POSITIF / KEGIATAN"
        )

    else:

        category = (
            "NETRAL / LAINNYA"
        )

        scope = "neutral"
        scope_label = (
            "NETRAL"
        )

    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    negative_hits = sum(
        1
        for term in NEGATIVE_OKNUM_TERMS
        if contains_term(
            text,
            term
        )
    )

    crime_hits = sum(
        1
        for term in CRIME_TERMS
        if contains_term(
            text,
            term
        )
    )

    ethic_hits = sum(
        1
        for term in ETHIC_TERMS
        if contains_term(
            text,
            term
        )
    )

    score = (
        negative_hits * 2
        + crime_hits
        + ethic_hits
    )

    if (
        is_negative_oknum
        and score >= 4
    ):

        priority = "high"

    elif (
        is_negative_oknum
        or score >= 2
    ):

        priority = "medium"

    else:

        priority = "low"

    return (
        is_jatim,
        polres,
        category,
        scope,
        scope_label,
        priority,
    )


# ============================================================
# QUERY BUILDER
# ============================================================

def build_queries():

    queries = list(
        GENERAL_QUERIES
    )

    # Tambahkan query eksplisit untuk masing-masing Polres.
    #
    # Ini meningkatkan kemungkinan berita lokal ditemukan
    # walaupun judul tidak memakai kata "oknum".

    for polres_name in POLRES:

        queries.append(
            f'"{polres_name.lower()}" polisi'
        )

    # Deduplicate query.

    result = []
    seen = set()

    for query in queries:

        key = query.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(query)

    return result


# ============================================================
# MAIN
# ============================================================

def main():

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

            print(
                "WARN: gagal membaca data lama:",
                exc
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

    collected_at = (
        dt.datetime.now(
            dt.timezone.utc
        ).isoformat()
    )

    # --------------------------------------------------------
    # RECLASSIFY EXISTING DATA
    # --------------------------------------------------------

    print(
        f"Reclassifying {len(items)} existing records..."
    )

    for item in items:

        if not isinstance(
            item,
            dict
        ):
            continue

        (
            is_jatim,
            polres,
            category,
            scope,
            scope_label,
            priority,
        ) = classify_article(
            item.get(
                "title",
                ""
            ),
            item.get(
                "summary",
                ""
            )
        )

        item["is_jatim"] = (
            is_jatim
        )

        item["region"] = (
            "Jawa Timur"
            if is_jatim
            else "Indonesia"
        )

        # Jika Jatim tetapi Polres tidak
        # terdeteksi, polres tetap None.
        #
        # DATA TIDAK DIHAPUS.

        item["polres"] = (
            polres
        )

        item["category"] = (
            category
        )

        item["scope"] = (
            scope
        )

        item["scope_label"] = (
            scope_label
        )

        item["priority"] = (
            priority
        )

    # --------------------------------------------------------
    # COLLECT NEW NEWS
    # --------------------------------------------------------

    queries = build_queries()

    added = 0

    print(
        f"Running {len(queries)} queries..."
    )

    for index, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"[{index}/{len(queries)}] {query}"
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

                identity = hashlib.sha1(
                    (
                        title
                        + "|"
                        + link
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()

                if identity in seen:
                    continue

                searchable_text = (
                    title
                    + " "
                    + description
                ).lower()

                # Pastikan artikel memang berkaitan
                # dengan polisi/Polri.

                if not any(
                    contains_term(
                        searchable_text,
                        term
                    )
                    for term in [
                        "polisi",
                        "polri",
                        "oknum",
                    ]
                ):
                    continue

                published_at = parse_date(
                    article.findtext(
                        "pubDate"
                    )
                )

                source = clean(
                    article.findtext(
                        "source"
                    )
                )

                if not source:
                    source = "Google News"

                (
                    is_jatim,
                    polres,
                    category,
                    scope,
                    scope_label,
                    priority,
                ) = classify_article(
                    title,
                    description
                )

                item = {
                    "id": identity,
                    "title": title,
                    "url": link,
                    "source": source,
                    "published_at": published_at,
                    "collected_at": collected_at,
                    "region": (
                        "Jawa Timur"
                        if is_jatim
                        else "Indonesia"
                    ),
                    "is_jatim": is_jatim,
                    "polres": polres,
                    "category": category,
                    "scope": scope,
                    "scope_label": scope_label,
                    "priority": priority,
                    "summary": strip_html(
                        description
                    )[:700],
                }

                items.append(
                    item
                )

                seen.add(
                    identity
                )

                added += 1

        except Exception as exc:

            print(
                f"WARN: query gagal: "
                f"{query} -> {exc}"
            )

        time.sleep(
            0.15
        )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    items.sort(
        key=lambda item:
            item.get(
                "published_at",
                ""
            ),
        reverse=True
    )

    # Simpan maksimal 5.000 berita terbaru.

    items = items[:5000]

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

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
            {
                "generated_at": collected_at,
                "items": items,
            },
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        "=========================================="
    )

    print(
        f"Existing records : {len(items) - added}"
    )

    print(
        f"New records      : {added}"
    )

    print(
        f"Total records    : {len(items)}"
    )

    print(
        "==========================================" 
    )


if __name__ == "__main__":
    main()
