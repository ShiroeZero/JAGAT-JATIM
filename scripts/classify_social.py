import re


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


# ============================================================
# NOISE
# ============================================================

NOISE_PATTERNS = [
    r"\balur cerita\b",
    r"\bmovie recap\b",
    r"\bfilm recap\b",
    r"\brecap film\b",
    r"\bcerita film\b",
    r"\bfilm\b.*\bpolisi\b",
    r"\bpolisi\b.*\bfilm\b",
    r"\bfiction\b",
    r"\bfiksi\b",
    r"\bparodi\b",
    r"\bkomedi\b",
    r"\bremix\b",
    r"\bdubbing\b",
    r"\bgame\b",
    r"\bgaming\b",
    r"\bmainan\b",
    r"\bchallenge\b",
    r"\bmeme\b",
]


# ============================================================
# POLISI SEBAGAI KORBAN
# ============================================================

VICTIM_PATTERNS = [

    r"\bpolisi\b.{0,100}\bditembak\b",
    r"\bpolisi\b.{0,100}\btertembak\b",

    r"\bpolisi\b.{0,100}\bdiserang\b",
    r"\bpolisi\b.{0,100}\bdianiaya\b",
    r"\bpolisi\b.{0,100}\bdikeroyok\b",

    r"\bpolisi\b.{0,100}\bterluka\b",
    r"\bpolisi\b.{0,100}\bluka\b",

    r"\bpolisi\b.{0,100}\btewas\b",
    r"\bpolisi\b.{0,100}\bmeninggal\b",

    r"\banggota polisi\b.{0,100}\bkorban\b",
    r"\banggota polri\b.{0,100}\bkorban\b",

    r"\bpolisi\b.{0,100}\bmenjadi korban\b",
    r"\bpolisi\b.{0,100}\bjadi korban\b",

    r"\bpolisi\b.{0,100}\bbaku tembak\b",

    r"\b3 polisi\b.{0,100}\bluka\b",
    r"\b3 polisi\b.{0,100}\bterluka\b",

    r"\banggota\b.{0,50}\bpolisi\b.{0,100}\bterluka\b",
]


# ============================================================
# POLISI SEBAGAI PENINDAK
# ============================================================

ENFORCER_PATTERNS = [

    r"\bditangkap polisi\b",
    r"\bditangkap oleh polisi\b",

    r"\bdiamankan polisi\b",
    r"\bdiamankan oleh polisi\b",

    r"\bditangkap polri\b",
    r"\bdiamankan polri\b",

    r"\bpolisi menangkap\b",
    r"\bpolisi mengamankan\b",
    r"\bpolisi amankan\b",

    r"\bpolisi menetapkan\b",
    r"\bpolisi tetapkan\b",

    r"\bpolisi mengungkap\b",
    r"\bpolisi ungkap\b",

    r"\bpolisi menyita\b",
    r"\bpolisi sita\b",

    r"\bpolisi menggagalkan\b",

    r"\bpolisi membekuk\b",
    r"\bpolisi meringkus\b",
    r"\bpolisi ringkus\b",

    r"\bpolisi menangkap\b",

    r"\bpolisi memburu\b",
    r"\bpolisi buru\b",

    r"\bpolisi gerebek\b",
    r"\bpolisi menggerebek\b",

    r"\bpolisi menemukan\b",
    r"\bpolisi temukan\b",

    r"\bpolisi berhasil menangkap\b",
    r"\bpolisi berhasil mengungkap\b",

    r"\bpolisi tangkap\b",
    r"\bpolisi amankan\b",
]


# ============================================================
# POLISI SEBAGAI PELAKU
# ============================================================

OFFENDER_PATTERNS = [

    r"\boknum polisi\b",
    r"\boknum polri\b",

    r"\banggota polisi\b.{0,100}\btersangka\b",
    r"\banggota polri\b.{0,100}\btersangka\b",

    r"\banggota polisi\b.{0,100}\bterlibat\b",
    r"\banggota polri\b.{0,100}\bterlibat\b",

    r"\bpolisi\b.{0,80}\bjadi tersangka\b",
    r"\bpolisi\b.{0,80}\bmenjadi tersangka\b",

    r"\bpolisi\b.{0,100}\bterlibat korupsi\b",
    r"\bpolisi\b.{0,100}\bterlibat suap\b",
    r"\bpolisi\b.{0,100}\bterlibat pungli\b",

    r"\bpolisi\b.{0,100}\bterlibat narkoba\b",
    r"\bpolisi\b.{0,100}\bterlibat narkotika\b",

    r"\bpolisi\b.{0,100}\bmelakukan penganiayaan\b",
    r"\bpolisi\b.{0,100}\bmelakukan kekerasan\b",
    r"\bpolisi\b.{0,100}\bmelakukan pungli\b",
    r"\bpolisi\b.{0,100}\bmelakukan pemerasan\b",

    r"\bpolisi\b.{0,100}\bpelanggaran etik\b",
    r"\bpolisi\b.{0,100}\bpelanggaran disiplin\b",

    r"\bpolisi\b.{0,100}\bpenyalahgunaan wewenang\b",

    r"\bpolisi\b.{0,100}\bditahan karena\b",
    r"\bpolisi\b.{0,100}\bditangkap karena\b",
]


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


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def match_any(text, patterns):
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def contains_word(text, term):
    return re.search(
        r"(?<![a-z0-9])"
        + re.escape(term)
        + r"(?![a-z0-9])",
        text,
    ) is not None


def classify(title, description=""):

    title = normalize(title)
    description = normalize(description)

    text = f"{title} {description}"

    # ========================================================
    # 1. NOISE
    # ========================================================

    if match_any(text, NOISE_PATTERNS):

        return {
            "scope": "noise",
            "category": "Tidak Relevan",
            "role": "noise",
            "confidence": 95,
            "reason": [
                "konten non-berita"
            ],
        }

    # ========================================================
    # 2. POLISI KORBAN
    #
    # HARUS sebelum negative.
    # ========================================================

    if match_any(text, VICTIM_PATTERNS):

        return {
            "scope": "incident",
            "category": "Peristiwa Melibatkan Polisi",
            "role": "victim",
            "confidence": 95,
            "reason": [
                "polisi sebagai korban"
            ],
        }

    # ========================================================
    # 3. POLISI PELAKU
    #
    # Diperiksa sebelum enforcer untuk menghindari:
    #
    # "polisi ditangkap karena narkoba"
    #
    # menjadi case.
    # ========================================================

    if match_any(text, OFFENDER_PATTERNS):

        if any(
            contains_word(text, keyword)
            for keyword in NEGATIVE_KEYWORDS
        ):

            if any(
                contains_word(
                    text,
                    keyword,
                )
                for keyword in [
                    "korupsi",
                    "suap",
                    "pungli",
                    "pemerasan",
                ]
            ):

                category = "Oknum / Korupsi / Pungli"

            elif any(
                contains_word(
                    text,
                    keyword,
                )
                for keyword in [
                    "narkoba",
                    "narkotika",
                    "sabu",
                ]
            ):

                category = "Oknum / Narkoba"

            elif any(
                contains_word(
                    text,
                    keyword,
                )
                for keyword in [
                    "pelanggaran etik",
                    "pelanggaran disiplin",
                ]
            ):

                category = "Etik / Disiplin"

            elif any(
                contains_word(
                    text,
                    keyword,
                )
                for keyword in [
                    "penganiayaan",
                    "kekerasan",
                ]
            ):

                category = "Kekerasan / Penganiayaan"

            elif contains_word(
                text,
                "penyalahgunaan wewenang",
            ):

                category = "Penyalahgunaan Wewenang"

            else:

                category = "Oknum / Pelanggaran Anggota"

            return {
                "scope": "negative",
                "category": category,
                "role": "offender",
                "confidence": 95,
                "reason": [
                    "polisi sebagai pelaku"
                ],
            }

    # ========================================================
    # 4. POLISI PENINDAK
    # ========================================================

    if match_any(text, ENFORCER_PATTERNS):

        return {
            "scope": "case",
            "category": "Ungkap Kasus",
            "role": "enforcer",
            "confidence": 95,
            "reason": [
                "polisi sebagai penindak"
            ],
        }

    # ========================================================
    # 5. POLISI TERKAIT PERISTIWA
    # ========================================================

    event_terms = [
        "polisi baku tembak",
        "polisi dikepung",
        "polisi terlibat kecelakaan",
        "polisi kecelakaan",
        "polisi kebakaran",
        "polisi evakuasi",
        "polisi membantu korban",
    ]

    if any(
        contains_word(text, term)
        for term in event_terms
    ):

        return {
            "scope": "incident",
            "category": "Peristiwa Melibatkan Polisi",
            "role": "general_incident",
            "confidence": 80,
            "reason": [
                "peristiwa melibatkan polisi"
            ],
        }

    # ========================================================
    # 6. POLISI UMUM
    # ========================================================

    if any(
        contains_word(text, term)
        for term in POLRI_TERMS
    ):

        return {
            "scope": "neutral",
            "category": "Berita Polisi Lainnya",
            "role": "general",
            "confidence": 65,
            "reason": [
                "polisi disebut",
            ],
        }

    # ========================================================
    # 7. REVIEW
    # ========================================================

    return {
        "scope": "review",
        "category": "Perlu Review",
        "role": "ambiguous",
        "confidence": 40,
        "reason": [
            "hubungan polisi tidak cukup jelas",
        ],
    }


def detect_priority(classification, title, description=""):

    if classification["scope"] != "negative":
        return "low"

    text = normalize(
        f"{title} {description}"
    )

    high = [
        "korupsi",
        "suap",
        "pungli",
        "narkoba",
        "narkotika",
        "sabu",
        "tewas",
        "meninggal",
        "penembakan",
    ]

    medium = [
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
        contains_word(text, term)
        for term in high
    ):
        return "high"

    if any(
        contains_word(text, term)
        for term in medium
    ):
        return "medium"

    return "low"
