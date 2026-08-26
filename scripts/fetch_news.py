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
USER_AGENT = "PNM-Polri-Negative-News-Monitor/4.0"

# ============================================================
# QUERY MONITORING
# ============================================================

GENERAL_QUERIES = [
    '"oknum polisi" Indonesia',
    '"oknum Polri" Indonesia',
    '"anggota polisi" ditangkap',
    '"anggota Polri" tersangka',
    '"polisi" "ditetapkan sebagai tersangka"',
    '"polisi" "pelanggaran etik"',
    '"polisi" "pelanggaran disiplin"',
    '"polisi" narkoba',
    '"polisi" korupsi',
    '"polisi" pungli',
    '"polisi" pemerasan',
    '"polisi" penganiayaan',
    '"polisi" penembakan',
    '"polisi" kekerasan',
    '"polisi" penyalahgunaan wewenang',
    '"polisi" suap',
    '"polisi" diperiksa Propam',
    '"polisi" dipecat',
    '"polisi" diberhentikan',
    '"polisi" ungkap kasus',
    '"polisi" tangkap pelaku',
    '"polisi" amankan tersangka',
    '"polisi" Jawa Timur',
    '"oknum polisi" Jawa Timur',
]

# ============================================================
# 39 POLRES JAWA TIMUR
# ============================================================

POLRES = {
    "POLRES PELABUHAN TANJUNG PERAK": [
        "polres pelabuhan tanjung perak",
        "polres tanjung perak",
        "pelabuhan tanjung perak",
    ],

    "POLRES JEMBER": [
        "polres jember",
        "polres kabupaten jember",
        "kabupaten jember",
    ],

    "POLRES KEDIRI KOTA": [
        "polres kediri kota",
        "polresta kediri",
        "kepolisian resor kediri kota",
        "kota kediri",
    ],

    "POLRES KEDIRI": [
        "polres kediri",
        "kepolisian resor kediri",
        "kabupaten kediri",
    ],

    "POLRES BLITAR KOTA": [
        "polres blitar kota",
        "polresta blitar",
        "kepolisian resor blitar kota",
        "kota blitar",
    ],

    "POLRES BLITAR": [
        "polres blitar",
        "kepolisian resor blitar",
        "kabupaten blitar",
    ],

    "POLRESTABES SURABAYA": [
        "polrestabes surabaya",
        "polres kota besar surabaya",
        "kepolisian resor kota besar surabaya",
        "kota surabaya",
        "surabaya",
    ],

    "POLRESTA MALANG KOTA": [
        "polresta malang kota",
        "polresta malang",
        "polres malang kota",
        "kepolisian resor kota malang",
        "kota malang",
        "malang kota",
    ],

    "POLRES MALANG": [
        "polres malang",
        "kepolisian resor malang",
        "kabupaten malang",
    ],

    "POLRESTA SIDOARJO": [
        "polresta sidoarjo",
        "polres sidoarjo",
        "kepolisian resor kota sidoarjo",
        "kabupaten sidoarjo",
        "sidoarjo",
    ],

    "POLRESTA BANYUWANGI": [
        "polresta banyuwangi",
        "polres banyuwangi",
        "kepolisian resor kota banyuwangi",
        "kabupaten banyuwangi",
        "banyuwangi",
    ],

    "POLRESTA TUBAN": [
        "polresta tuban",
        "polres tuban",
        "kepolisian resor tuban",
        "kabupaten tuban",
        "tuban",
    ],

    "POLRESTA SUMENEP": [
        "polresta sumenep",
        "polres sumenep",
        "kepolisian resor sumenep",
        "kabupaten sumenep",
        "sumenep",
    ],

    "POLRES GRESIK": [
        "polres gresik",
        "kepolisian resor gresik",
        "kabupaten gresik",
        "gresik",
    ],

    "POLRES PASURUAN KOTA": [
        "polres pasuruan kota",
        "polresta pasuruan",
        "kepolisian resor kota pasuruan",
        "kota pasuruan",
        "pasuruan kota",
    ],

    "POLRES PASURUAN": [
        "polres pasuruan",
        "kepolisian resor pasuruan",
        "kabupaten pasuruan",
    ],

    "POLRES PROBOLINGGO KOTA": [
        "polres probolinggo kota",
        "polresta probolinggo",
        "kepolisian resor kota probolinggo",
        "kota probolinggo",
        "probolinggo kota",
    ],

    "POLRES PROBOLINGGO": [
        "polres probolinggo",
        "kepolisian resor probolinggo",
        "kabupaten probolinggo",
    ],

    "POLRES LUMAJANG": [
        "polres lumajang",
        "kepolisian resor lumajang",
        "kabupaten lumajang",
        "lumajang",
    ],

    "POLRES BATU": [
        "polres batu",
        "polresta batu",
        "kepolisian resor batu",
        "kota batu",
        "batu",
    ],

    "POLRES BONDOWOSO": [
        "polres bondowoso",
        "kepolisian resor bondowoso",
        "kabupaten bondowoso",
        "bondowoso",
    ],

    "POLRES SITUBONDO": [
        "polres situbondo",
        "kepolisian resor situbondo",
        "kabupaten situbondo",
        "situbondo",
    ],

    "POLRES TULUNGAGUNG": [
        "polres tulungagung",
        "kepolisian resor tulungagung",
        "kabupaten tulungagung",
        "tulungagung",
    ],

    "POLRES NGANJUK": [
        "polres nganjuk",
        "kepolisian resor nganjuk",
        "kabupaten nganjuk",
        "nganjuk",
    ],

    "POLRES TRENGGALEK": [
        "polres trenggalek",
        "kepolisian resor trenggalek",
        "kabupaten trenggalek",
        "trenggalek",
    ],

    "POLRES MADIUN KOTA": [
        "polres madiun kota",
        "polresta madiun",
        "kepolisian resor kota madiun",
        "kota madiun",
        "madiun kota",
    ],

    "POLRES MADIUN": [
        "polres madiun",
        "kepolisian resor madiun",
        "kabupaten madiun",
    ],

    "POLRES NGAWI": [
        "polres ngawi",
        "kepolisian resor ngawi",
        "kabupaten ngawi",
        "ngawi",
    ],

    "POLRES MAGETAN": [
        "polres magetan",
        "kepolisian resor magetan",
        "kabupaten magetan",
        "magetan",
    ],

    "POLRES PONOROGO": [
        "polres ponorogo",
        "kepolisian resor ponorogo",
        "kabupaten ponorogo",
        "ponorogo",
    ],

    "POLRES PACITAN": [
        "polres pacitan",
        "kepolisian resor pacitan",
        "kabupaten pacitan",
        "pacitan",
    ],

    "POLRES BOJONEGORO": [
        "polres bojonegoro",
        "kepolisian resor bojonegoro",
        "kabupaten bojonegoro",
        "bojonegoro",
    ],

    "POLRES LAMONGAN": [
        "polres lamongan",
        "kepolisian resor lamongan",
        "kabupaten lamongan",
        "lamongan",
    ],

    "POLRES MOJOKERTO KOTA": [
        "polres mojokerto kota",
        "polresta mojokerto",
        "kepolisian resor kota mojokerto",
        "kota mojokerto",
        "mojokerto kota",
    ],

    "POLRES MOJOKERTO": [
        "polres mojokerto",
        "kepolisian resor mojokerto",
        "kabupaten mojokerto",
    ],

    "POLRES JOMBANG": [
        "polres jombang",
        "kepolisian resor jombang",
        "kabupaten jombang",
        "jombang",
    ],

    "POLRES PAMEKASAN": [
        "polres pamekasan",
        "kepolisian resor pamekasan",
        "kabupaten pamekasan",
        "pamekasan",
    ],

    "POLRES BANGKALAN": [
        "polres bangkalan",
        "kepolisian resor bangkalan",
        "kabupaten bangkalan",
        "bangkalan",
    ],

    "POLRES SAMPANG": [
        "polres sampang",
        "kepolisian resor sampang",
        "kabupaten sampang",
        "sampang",
    ],
}

# Alias terpanjang diperiksa lebih dahulu.
# Ini penting untuk membedakan:
# POLRES KEDIRI KOTA vs POLRES KEDIRI
# POLRES BLITAR KOTA vs POLRES BLITAR
# dst.
POLRES_ALIASES = sorted(
    [
        (name, alias)
        for name, aliases in POLRES.items()
        for alias in aliases
    ],
    key=lambda item: len(item[1]),
    reverse=True,
)

JATIM_TERMS = [
    "jawa timur",
    "jatim",
    "polda jatim",
    "polda jawa timur",
]

# Wilayah yang secara eksplisit bukan Jawa Timur.
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
# KLASIFIKASI
# ============================================================

NEGATIVE_OKNUM = [
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
    "etik",
    "disiplin",
    "propam",
    "pelanggaran disiplin",
    "pelanggaran etik",
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

PERFORMANCE_TERMS = [
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
# UTILITAS
# ============================================================

def parse_date(value):
    try:
        return parsedate_to_datetime(value).astimezone(
            dt.timezone.utc
        ).isoformat()
    except Exception:
        return dt.datetime.now(
            dt.timezone.utc
        ).isoformat()


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


def get(url):
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urlopen(request, timeout=20) as response:
        return response.read()


def contains_term(text, term):
    term = term.lower().strip()

    if " " in term:
        return term in text

    return (
        re.search(
            r"(?<![a-z])"
            + re.escape(term)
            + r"(?![a-z])",
            text
        )
        is not None
    )


# ============================================================
# DETEKSI POLRES
# ============================================================

def find_polres(text):
    """
    Mencari Polres berdasarkan judul + description.

    Alias paling spesifik diperiksa lebih dahulu.
    """

    for name, alias in POLRES_ALIASES:
        if contains_term(text, alias):
            return name

    return None


# ============================================================
# DETEKSI JAWA TIMUR
# ============================================================

def classify_region(text, polres):
    """
    SOURCE/MEDIA TIDAK DIGUNAKAN.

    Hanya:
    - judul
    - description/article text
    """

    non_jatim_hits = [
        term
        for term in NON_JATIM_TERMS
        if contains_term(text, term)
    ]

    jatim_hits = [
        term
        for term in JATIM_TERMS
        if contains_term(text, term)
    ]

    # Polres Jatim adalah bukti paling kuat.
    if polres:
        return True

    # Artikel menyebut Jatim/Polda Jatim.
    if jatim_hits:

        # Jika ada wilayah luar Jatim yang eksplisit,
        # jangan paksa menjadi Jatim.
        if non_jatim_hits:
            return False

        return True

    # Tidak ada bukti cukup untuk Jatim.
    return False


# ============================================================
# KLASIFIKASI ARTIKEL
# ============================================================

def classify_article(title, description):

    text = clean(
        (title or "")
        + " "
        + strip_html(description or "")
    ).lower()

    # ----------------------------
    # POLRES
    # ----------------------------

    polres = find_polres(text)

    # ----------------------------
    # JAWA TIMUR
    # ----------------------------

    is_jatim = classify_region(
        text,
        polres
    )

    # ----------------------------
    # NEGATIF OKNUM
    # ----------------------------

    negative_oknum = any(
        contains_term(text, term)
        for term in NEGATIVE_OKNUM
    )

    if negative_oknum:

        if any(
            contains_term(text, term)
            for term in ETHIC_TERMS
        ):
            category = "OKNUM - ETIK/DISIPLIN"

        elif any(
            contains_term(text, term)
            for term in ABUSE_TERMS
        ):
            category = "OKNUM - PENYALAHGUNAAN WEWENANG"

        else:
            category = "OKNUM - PIDANA"

        scope = "negative"
        scope_label = "NEGATIF / OKNUM"

    # ----------------------------
    # NEGATIF KINERJA
    # ----------------------------

    elif any(
        contains_term(text, term)
        for term in SERVICE_NEGATIVE_TERMS
    ):
        category = "KINERJA/LAYANAN POLRI"
        scope = "negative"
        scope_label = "NEGATIF / KINERJA"

    # ----------------------------
    # UNGKAP KASUS
    # ----------------------------

    elif any(
        contains_term(text, term)
        for term in CASE_TERMS
    ):
        category = "UNGKAP KASUS / PENINDAKAN"
        scope = "case"
        scope_label = "UNGKAP KASUS"

    # ----------------------------
    # POSITIF / KEGIATAN
    # ----------------------------

    elif any(
        contains_term(text, term)
        for term in PERFORMANCE_TERMS
    ):
        category = "PRESTASI / KEGIATAN POSITIF"
        scope = "positive"
        scope_label = "POSITIF / KEGIATAN"

    # ----------------------------
    # NETRAL
    # ----------------------------

    else:
        category = "NETRAL / LAINNYA"
        scope = "neutral"
        scope_label = "NETRAL"

    # ========================================================
    # PRIORITAS
    # ========================================================

    negative_hits = sum(
        1
        for term in NEGATIVE_OKNUM
        if contains_term(text, term)
    )

    crime_hits = sum(
        1
        for term in CRIME_TERMS
        if contains_term(text, term)
    )

    ethic_hits = sum(
        1
        for term in ETHIC_TERMS
        if contains_term(text, term)
    )

    score = (
        negative_hits * 2
        + crime_hits
        + ethic_hits
    )

    if negative_oknum and score >= 4:
        priority = "high"

    elif negative_oknum or score >= 2:
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
# QUERY PER POLRES
# ============================================================

def build_queries():

    queries = list(
        GENERAL_QUERIES
    )

    # Tambahkan pencarian khusus masing-masing Polres.
    #
    # Ini penting karena berita lokal sering tidak memakai
    # kata "oknum" pada judul.

    for polres_name, aliases in POLRES.items():

        queries.append(
            f'"{polres_name.lower()}" polisi'
        )

        if aliases:
            queries.append(
                f'"{aliases[0]}" polisi'
            )

    # Deduplicate query.

    seen = set()
    result = []

    for query in queries:

        key = query.lower()

        if key not in seen:

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
    # LOAD DATA LAMA
    # --------------------------------------------------------

    if os.path.exists(OUT):

        try:

            with open(
                OUT,
                "r",
                encoding="utf-8"
            ) as file:

                old = json.load(file)

        except Exception as exc:

            print(
                f"WARN: gagal membaca {OUT}: {exc}"
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

    seen = {
        item.get("id")
        or item.get("url")

        for item in items

        if isinstance(
            item,
            dict
        )
    }

    collected_at = (
        dt.datetime.now(
            dt.timezone.utc
        ).isoformat()
    )

    # ========================================================
    # RECLASSIFY DATA LAMA
    # ========================================================

    print(
        f"Reclassifying {len(items)} existing records..."
    )

    for item in items:

        if not isinstance(
            item,
            dict
        ):
            continue

        title = item.get(
            "title",
            ""
        )

        description = item.get(
            "summary",
            ""
        )

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

        item["is_jatim"] = (
            is_jatim
        )

        item["region"] = (
            "Jawa Timur"
            if is_jatim
            else "Indonesia"
        )

        item["polres"] = polres

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

    # ========================================================
    # COLLECT BERITA BARU
    # ========================================================

    queries = build_queries()

    added = 0

    print(
        f"Running {len(queries)} search queries..."
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

            rss_root = ET.fromstring(
                rss_data
            )

            for article in rss_root.findall(
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

                # Pastikan berita berhubungan dengan Polri.

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

    # Maksimal 5.000 berita terbaru.

    items = items[:5000]

    # ========================================================
    # SAVE
    # ========================================================

    output = {
        "generated_at": collected_at,
        "items": items,
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

    print(
        "======================================"
    )

    print(
        f"Existing records reclassified : "
        f"{len(items) - added}"
    )

    print(
        f"New records added             : "
        f"{added}"
    )

    print(
        f"Total records                 : "
        f"{len(items)}"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()
