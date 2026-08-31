"""JAGAT V6.5.4 deterministic context-aware article/case analysis.

Core rule:
    Phrase/context > isolated keyword.

The engine separates:
- sentiment (positif/negatif/netral)
- issue taxonomy
- relation of Polri to the event
- handling status
- attention score 0-100
- operational level: rendah/sedang/tinggi

No external AI is required.
"""

import re
from collections import Counter

ATTENTION_BANDS = [
    (0, 39, "Rendah"),
    (40, 69, "Sedang"),
    (70, 100, "Tinggi"),
]

POSITIVE_PATTERNS = [
    ("Penegakan hukum berhasil", [
        r"\bberhasil\s+(?:menangkap|mengungkap|mengamankan|membekuk|meringkus|menggagalkan|menyita|memberantas)\b",
        r"\b(?:polisi|polres|polresta|polrestabes|polda)\b.{0,90}\b(?:berhasil|sukses)\b.{0,50}\b(?:ungkap|tangkap|amankan|gagalkan|sita|berantas)\b",
        r"\b(?:polisi|polres|polresta|polda)\b.{0,80}\b(?:tindak tegas|tindakan tegas)\b",
    ]),
    ("Operasi / pengungkapan", [
        r"\b(?:operasi|operasi tumpas|razia|pengungkapan)\b.{0,120}\b(?:ungkap|tangkap|amankan|sita|tersangka)\b",
    ]),
    ("Pelayanan / prestasi", [
        r"\b(?:pelayanan|inovasi|prestasi|penghargaan|apresiasi)\b.{0,100}\b(?:polisi|polres|polda|polri)\b",
        r"\b(?:polisi|polres|polda)\b.{0,100}\b(?:meraih|mendapat|menerima)\b.{0,60}\b(?:penghargaan|apresiasi|prestasi)\b",
    ]),
    ("Pemulihan / kompensasi", [
        r"\b(?:sudah|telah|resmi)\s+(?:dibayar|membayar|diberi(?:kan)?|menerima)\b.{0,100}\b(?:ganti\s+rugi|kompensasi|penggantian)\b",
        r"\b(?:dibayar|membayar)\b.{0,60}\b(?:\d+\s*(?:x|kali)\s*lipat|sepuluh\s+kali)\b",
        r"\b(?:ganti\s+rugi|kompensasi|penggantian)\b",
    ]),
]

ISSUE_PATTERNS = [
    ("INTEGRITAS_DAN_KEUANGAN", "Pungli / Suap / Pemerasan", [
        "pungli", "pungutan liar", "suap", "gratifikasi", "pemerasan",
        "memeras", "setoran", "upeti", "uang damai", "uang pelicin",
        "tarif bayangan", "sogokan", "lepas tangkap", "tangkap lepas",
        "tebusan", "minta uang", "minta bayaran",
    ]),
    ("PENYALAHGUNAAN_WEWENANG", "Penyalahgunaan Wewenang", [
        "penyalahgunaan wewenang", "menyalahgunakan wewenang",
        "salahgunakan wewenang", "kriminalisasi", "intervensi",
        "sewenang-wenang", "dibeking", "dibeckup", "backing",
        "tebang pilih", "kebal hukum", "bermain perkara", "tutupi laporan",
        "menutupi laporan", "menutup laporan", "mengabaikan laporan",
        "menghapus laporan", "memanipulasi laporan", "merekayasa kasus",
    ]),
    ("PROFESIONALISME_DAN_PROSEDUR", "Pelanggaran SOP / Prosedur", [
        "langgar sop", "melanggar sop", "pelanggaran sop", "tak sesuai sop",
        "tidak sesuai sop", "salah prosedur", "prosedur cacat", "salah tangkap",
        "ketidakprofesionalan", "tidak profesional", "maladministrasi",
        "salah tembak", "prosedur penangkapan", "prosedur penyidikan",
    ]),
    ("KEKERASAN_DAN_KEKUATAN", "Kekerasan / Penggunaan Kekuatan", [
        "penganiayaan", "kekerasan", "pemukulan", "penyiksaan", "penembakan",
        "menembak", "kekerasan fisik", "penggunaan senjata", "tembakan",
        "ditembak", "dikeroyok", "tewas", "dibunuh", "membunuh",
        "pembunuhan",
    ]),
    ("KEJAHATAN_SEKSUAL", "Kejahatan Seksual", [
        "pemerkosaan", "perkosaan", "pencabulan", "cabul", "kekerasan seksual",
        "pelecehan seksual", "eksploitasi seksual", "aborsi paksa",
        "seksual terhadap anak",
    ]),
    ("ETIK_DAN_PERILAKU", "Etik / Perilaku Personel", [
        "perselingkuhan", "selingkuh", "nikah siri", "hubungan gelap", "tiduri",
        "tidur dengan", "asusila", "kdrt", "mabuk", "pelanggaran etik",
    ]),
    ("KESEHATAN_REPRODUKSI", "Aborsi / Pemaksaan Kehamilan", [
        "aborsi", "menggugurkan", "gugurkan kandungan", "gugur kandungan",
        "memaksa aborsi", "perintah aborsi",
    ]),
    ("NARKOBA", "Narkoba / Narkotika", [
        "narkoba", "narkotika", "sabu", "ganja", "ekstasi", "obat terlarang",
    ]),
    ("AKTIVITAS_ILEGAL", "Aktivitas Ilegal", [
        "tambang ilegal", "galian c ilegal", "galian c", "judi online", "judol",
        "sabung ayam", "rokok ilegal", "solar subsidi", "bbm subsidi", "miras",
        "minuman keras", "aktivitas ilegal", "ilegal", "barang bukti hilang",
    ]),
    ("MEDIA_DAN_PERS", "Intimidasi / Hambatan terhadap Pers", [
        "intimidasi wartawan", "intimidasi jurnalis", "wartawan diintimidasi",
        "ancam wartawan", "ancaman terhadap wartawan", "halangi peliputan",
        "menghalangi peliputan", "tekanan media", "jurnalis diintimidasi",
    ]),
    ("KEAMANAN_DAN_KAMTIBMAS", "Gangguan Keamanan / Kamtibmas", [
        "demo ricuh", "demonstrasi ricuh", "kerusuhan", "bentrok", "tawuran",
        "massa menyerang", "pos polisi dibakar", "mako diserang",
        "markas polisi diserang", "molotov", "huru-hara", "ricuh",
        "penyerangan kantor polisi",
    ]),
    ("DISIPLIN_DAN_LAYANAN", "Disiplin / Layanan", [
        "pelanggaran disiplin", "calo sim", "jalur belakang sim", "pungli samsat",
        "jual beli stck", "pelayanan buruk", "keluhan polisi", "kelalaian",
    ]),
]

HANDLING_PATTERNS = [
    ("BELUM_DITANGANI", [
        "belum tersentuh", "belum ditangani", "belum ditindaklanjuti",
        "belum ada tindakan", "belum ada respons", "tak kunjung ditangani",
        "tidak kunjung ditangani", "tidak ditanggapi", "tidak digubris",
        "dibiarkan", "didiamkan", "laporan diabaikan", "belum diproses",
        "tak kunjung diproses", "belum ada penanganan", "belum digubris",
    ]),
    ("SEDANG_DITANGANI", [
        "sedang ditangani", "dalam penanganan", "sedang diperiksa",
        "sedang diselidiki", "tengah diselidiki", "ditangani polisi",
        "ditangani propam", "diproses propam", "sedang diproses",
        "ditindaklanjuti polisi", "didalami polisi", "didalami propam",
        "ditindaklanjuti",
    ]),
    ("SUDAH_DITINDAK", [
        "ditahan", "ditetapkan sebagai tersangka", "tersangka", "disidangkan",
        "sidang etik", "dipecat", "diberhentikan", "ptdh", "diproses pidana",
        "divonis",
    ]),
    ("SUDAH_DITANGANI", [
        "sudah ditangani", "telah ditangani", "sudah diproses",
        "telah diproses", "sudah ditindaklanjuti", "telah ditindaklanjuti",
        "sudah ditindak", "berhasil ditangani",
    ]),
]

ISSUE_BASE = {
    "INTEGRITAS_DAN_KEUANGAN": 24,
    "PENYALAHGUNAAN_WEWENANG": 23,
    "PROFESIONALISME_DAN_PROSEDUR": 15,
    "KEKERASAN_DAN_KEKUATAN": 28,
    "KEJAHATAN_SEKSUAL": 26,
    "ETIK_DAN_PERILAKU": 12,
    "KESEHATAN_REPRODUKSI": 16,
    "NARKOBA": 11,
    "AKTIVITAS_ILEGAL": 14,
    "MEDIA_DAN_PERS": 24,
    "KEAMANAN_DAN_KAMTIBMAS": 21,
    "DISIPLIN_DAN_LAYANAN": 9,
    "UMUM": 2,
}

SEVERE_EVENT_PATTERNS = [
    (30, "pembunuhan / korban meninggal", [
        "pembunuhan", "dibunuh", "membunuh", "tewas", "meninggal dunia",
    ]),
    (29, "kekerasan berat", [
        "penyiksaan", "penganiayaan berat", "penembakan", "ditembak", "kekerasan seksual",
    ]),
    (28, "kejahatan seksual", [
        "pemerkosaan", "perkosaan", "pencabulan anak", "pencabulan", "seksual terhadap anak",
    ]),
]

AUTHORITY_PATTERNS = [
    (20, ["kapolda", "kapolres", "pju", "pejabat utama"]),
    (17, ["kombes", "akbp", "kompol", "perwira"]),
    (14, ["kasat", "resnarkoba", "reskrim", "satres", "satlantas", "propam"]),
    (10, ["anggota polisi", "anggota polri", "oknum polisi", "oknum polri"]),
]

# Explicit phrase combinations are stronger than individual tokens.
SUBJECT_PATTERNS = [
    ("oknum polisi + dugaan", [
        r"\boknum\s+(?:polisi|polri)\b.{0,100}\b(?:diduga|dituduh|terlibat|melanggar|melakukan|meminta|menerima|menembak|menganiaya|mengintimidasi)\b",
    ]),
    ("anggota polisi + dugaan", [
        r"\banggota\s+(?:polisi|polri)\b.{0,100}\b(?:diduga|dituduh|terlibat|melanggar|melakukan|meminta|menerima|menembak|menganiaya|mengintimidasi)\b",
        r"\banggota\s+(?:resnarkoba|reskrim|satres|satlantas|propam)\b.{0,100}\b(?:diduga|terlibat|melanggar|melakukan|meminta|menerima|ditangkap|ditahan)\b",
    ]),
    ("perwira / pejabat + dugaan", [
        r"\b(?:perwira|kapolres|kapolda|pju|kompol|akbp|kombes)\b.{0,100}\b(?:diduga|dituduh|terlibat|melanggar|melakukan|meminta|menerima)\b",
    ]),
    ("polisi + dugaan", [
        r"\bpolisi\b.{0,80}\b(?:diduga|dituduh|terlibat|melanggar|melakukan)\b",
    ]),
]

ENFORCER_PATTERNS = [
    r"\b(?:polisi|polres|polresta|polrestabes|polda)\b.{0,100}\b(?:berhasil|menangkap|mengamankan|amankan|mengungkap|ungkap|menggagalkan|gagalkan|menyita|sita|menindak|tindak|menahan|menetapkan|memproses)\b",
    r"\b(?:polres|polresta|polrestabes|polda)\b.{0,100}\b(?:operasi|razia)\b.{0,100}\b(?:tangkap|ungkap|amankan|sita|tersangka)\b",
]

POLICE_SUBJECT_NEGATIVE_HINTS = [
    "oknum polisi", "oknum polri", "anggota polisi", "anggota polri",
    "anggota resnarkoba", "anggota reskrim", "perwira polisi", "pju",
    "kapolres diduga", "kapolda diduga", "polisi diduga", "polisi terlibat",
]

SEVERE_NEGATIVE_ISSUES = {
    "INTEGRITAS_DAN_KEUANGAN",
    "PENYALAHGUNAAN_WEWENANG",
    "KEKERASAN_DAN_KEKUATAN",
    "KEJAHATAN_SEKSUAL",
    "MEDIA_DAN_PERS",
}

RISKY_MISCONDUCT_TERMS = {
    "pungli", "suap", "pemerasan", "setoran", "upeti", "lepas tangkap",
    "tangkap lepas", "tebusan", "penyalahgunaan wewenang", "langgar sop",
    "melanggar sop", "intimidasi wartawan", "intimidasi jurnalis",
    "penyiksaan", "penganiayaan", "penembakan", "mabuk", "perselingkuhan",
    "asusila", "aborsi", "pencabulan",
}

PROCEDURAL_NEUTRAL_PATTERNS = [
    r"\b(?:pengambilan|penyerahan|pengembalian|serah\s+terima)\s+barang\s+bukti\b",
    r"\b(?:mengambil|menyerahkan|mengembalikan)\s+barang\s+bukti\b",
]

PROCEDURAL_NEGATIVE_PATTERNS = [
    r"\bbarang\s+bukti\b.{0,60}\b(?:hilang|raib|dicuri|disalahgunakan)\b",
    r"\b(?:pengambilan|penyerahan|penyitaan|pengembalian)\b.{0,70}\b(?:ilegal|tidak\s+sah|melanggar\s+sop|salah\s+prosedur)\b",
]


def norm(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def has(text, phrase):
    return re.search(
        r"(?<![a-z0-9])" + re.escape(norm(phrase)) + r"(?![a-z0-9])",
        norm(text),
    ) is not None


def has_nonnegated(text, phrase):
    t = norm(text)
    p = norm(phrase)
    pattern = r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])"
    for match in re.finditer(pattern, t):
        prefix = t[max(0, match.start() - 42):match.start()]
        if re.search(r"\b(?:tidak|tak|bukan|tanpa)\b(?:\s+\w+){0,3}\s*$", prefix):
            continue
        return True
    return False


def any_phrase(text, phrases):
    return any(has(text, phrase) for phrase in phrases)


def attention_label(score):
    score = max(0, min(100, int(round(score or 0))))
    for low, high, label in ATTENTION_BANDS:
        if low <= score <= high:
            return label
    return "Tinggi"


def legacy_priority(score):
    score = int(round(score or 0))
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def first_issue(text):
    # Explicit contextual phrases outrank isolated words.
    combo_patterns = [
        (
            "INTEGRITAS_DAN_KEUANGAN",
            "Dugaan Imbalan untuk Pelepasan Tersangka",
            r"\b(?:minta|meminta|menerima|terima)\b.{0,60}\b(?:rp\s*[0-9]+|[0-9][0-9\.,]*\s*(?:juta|ribu|miliar))\b.{0,80}\b(?:lepas|melepaskan)\b",
        ),
        (
            "INTEGRITAS_DAN_KEUANGAN",
            "Dugaan Lepas Tangkap / Imbalan",
            r"\b(?:lepas|lepaskan|melepaskan)\b.{0,80}\b(?:tersangka|tahanan|pelaku)\b.{0,80}\b(?:uang|rp|juta|ribu|miliar|setoran|tebusan)\b",
        ),
        (
            "PROFESIONALISME_DAN_PROSEDUR",
            "Dugaan Pelanggaran SOP",
            r"\b(?:langgar|melanggar|pelanggaran|tak sesuai|tidak sesuai)\b.{0,40}\bsop\b",
        ),
    ]
    for issue_type, subtype, pattern in combo_patterns:
        if re.search(pattern, text):
            return issue_type, subtype, [pattern]

    best = None
    for issue_type, subtype, terms in ISSUE_PATTERNS:
        hits = [term for term in terms if has_nonnegated(text, term)]
        if not hits:
            continue
        strength = max(len(x) for x in hits)
        rank = 0 if issue_type == "NARKOBA" else 1
        candidate = (strength, rank, issue_type, subtype, hits)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    if best:
        return best[2], best[3], best[4][:5]
    return "UMUM", "Belum Teridentifikasi", []


def detect_handling(text):
    for status, terms in HANDLING_PATTERNS:
        hits = [term for term in terms if has_nonnegated(text, term)]
        if hits:
            points = {
                "BELUM_DITANGANI": 8,
                "SEDANG_DITANGANI": 4,
                "SUDAH_DITINDAK": 2,
                "SUDAH_DITANGANI": 1,
            }[status]
            return status, hits[:4], points
    return "BELUM_ADA_INFORMASI", [], 0


def detect_positive(text):
    for label, patterns in POSITIVE_PATTERNS:
        hits = [pattern for pattern in patterns if re.search(pattern, text)]
        if hits:
            return label, hits[:3]
    return None, []


def detect_procedural_context(text):
    if any(re.search(pattern, text) for pattern in PROCEDURAL_NEGATIVE_PATTERNS):
        return None, []
    hits = [pattern for pattern in PROCEDURAL_NEUTRAL_PATTERNS if re.search(pattern, text)]
    if hits:
        return "Prosedur barang bukti", hits[:3]
    return None, []


def detect_role(text):
    # Negative subject must take precedence over enforcement.
    for role_label, patterns in SUBJECT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text):
                return "SUBJEK_PERMASALAHAN", role_label

    for pattern in ENFORCER_PATTERNS:
        if re.search(pattern, text):
            return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak"

    procedural_label, _procedural_hits = detect_procedural_context(text)
    if procedural_label and any_phrase(text, ["polisi", "polres", "polresta", "polrestabes", "polda"]):
        return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak dalam prosedur barang bukti"

    if re.search(r"\bpolisi\b.{0,60}\b(?:ditembak|tertembak|diserang|dianiaya|dikeroyok|terluka|tewas|meninggal)\b", text):
        return "KORBAN", "Polisi sebagai korban"

    if any_phrase(text, [
        "belum tersentuh", "belum ditangani", "belum ada tindakan",
        "belum ada respons", "tak kunjung ditangani", "tidak ditanggapi",
        "tidak digubris", "dibiarkan", "didiamkan", "laporan diabaikan",
    ]) and has(text, "polisi"):
        return "RESPONS_TERHADAP_ISU", "Isu respons penanganan Polri"

    return "INFORMASI_UMUM", "Hubungan Polri belum spesifik"


def severity_analysis(text, issue_type, role):
    # A serious event in a neutral/enforcement article is not automatically
    # a serious institutional attention case.
    issue_base = ISSUE_BASE.get(issue_type, 2)
    hits = []
    severe_score = 0
    for points, label, terms in SEVERE_EVENT_PATTERNS:
        matched = [term for term in terms if has(text, term)]
        if matched:
            severe_score = max(severe_score, points)
            hits.append(label)

    if role == "SUBJEK_PERMASALAHAN" and severe_score:
        return severe_score, hits[:3]

    if severe_score and role in {"PENEGAKAN_HUKUM", "KORBAN"}:
        return min(18, severe_score // 2), hits[:3]

    modifiers = 0
    if has(text, "serius") or has(text, "berat"):
        modifiers += 2
    if has(text, "berulang") or has(text, "berulang kali"):
        modifiers += 2
    if any_phrase(text, ["lepas tangkap", "tangkap lepas"]):
        issue_base = max(issue_base, 20)
    if issue_type == "PROFESIONALISME_DAN_PROSEDUR" and any_phrase(text, ["langgar sop", "melanggar sop"]):
        issue_base = max(issue_base, 16)
    return min(30, issue_base + min(4, modifiers)), hits


def relation_analysis(text, role, issue_type):
    if role == "SUBJEK_PERMASALAHAN":
        if issue_type == "INTEGRITAS_DAN_KEUANGAN" or any_phrase(text, ["penyalahgunaan wewenang", "intimidasi wartawan"]):
            return 20, ["Polri/personel menjadi subjek masalah yang serius"]
        if any_phrase(text, ["perwira", "pju", "kapolres", "kapolda", "kompol", "akbp", "kombes"]):
            return 18, ["melibatkan pejabat/perwira"]
        return 16, ["Polri/personel menjadi subjek permasalahan"]
    if role == "KORBAN":
        return 6, ["Polisi sebagai korban"]
    if role == "RESPONS_TERHADAP_ISU":
        return 8, ["terdapat isu terkait respons penanganan Polri"]
    if role == "PENEGAKAN_HUKUM":
        return 2, ["Polri sebagai pihak penindak"]
    return 0, []


def authority_analysis(text):
    for points, terms in AUTHORITY_PATTERNS:
        hits = [term for term in terms if has(text, term)]
        if hits:
            return points, hits[:4]
    return 0, []


def impact_analysis(text, role, issue_type):
    if any_phrase(text, ["kepercayaan publik", "kepercayaan masyarakat", "meresahkan masyarakat", "masyarakat luas"]):
        return 20, ["dampak publik/institusional tinggi"]
    if any_phrase(text, ["wartawan", "jurnalis", "anak", "korban jiwa"]):
        return 18, ["kelompok/korban publik rentan"]
    if any_phrase(text, ["warga", "masyarakat", "kerugian", "laporan"]):
        return 12, ["dampak kepada masyarakat"]
    if role == "SUBJEK_PERMASALAHAN":
        return 10, ["dampak institusional"]
    if issue_type in {"KEAMANAN_DAN_KAMTIBMAS", "KEJAHATAN_SEKSUAL"}:
        return 10, ["dampak peristiwa"]
    return 4, []


def evidence_analysis(text):
    score = 1
    hits = ["satu sumber / informasi awal"]
    if any_phrase(text, ["klarifikasi", "menanggapi", "kata polisi", "ujar polisi", "menurut polisi"]):
        score += 2
        hits.append("ada tanggapan/klarifikasi")
    if any_phrase(text, ["propam", "diperiksa", "pemeriksaan", "penyelidikan", "penyidikan", "sidang etik"]):
        score += 2
        hits.append("ada tindak lanjut resmi")
    return min(5, score), hits


def nominal_amount(text):
    # Extract simple Indonesian currency forms: Rp50 juta, Rp 1,5 miliar, 500 ribu.
    matches = re.findall(
        r"\brp\s*[0-9][0-9\.,]*\s*(?:triliun|miliar|juta|ribu)?\b|\b[0-9][0-9\.,]*\s*(?:triliun|miliar|juta|ribu)\b",
        text,
    )
    return matches[:3]


def context_risk_bonus(text, issue_type, role):
    bonus = 0
    hits = []

    if role != "SUBJEK_PERMASALAHAN":
        return 0, []

    # Strong combined phrases. One matching family is enough; don't stack
    # every synonym in the sentence.
    if issue_type == "INTEGRITAS_DAN_KEUANGAN" and any_phrase(
        text, ["lepas tangkap", "tangkap lepas", "pungli", "suap", "pemerasan", "setoran", "upeti"]
    ):
        bonus += 10
        hits.append("dugaan pelanggaran integritas/keuangan oleh personel")
        amounts = nominal_amount(text)
        if amounts:
            bonus += 4
            hits.append("terdapat nominal/imbalan yang disebut")

    if issue_type == "PROFESIONALISME_DAN_PROSEDUR" and any_phrase(text, ["langgar sop", "melanggar sop", "salah prosedur", "salah tangkap"]):
        bonus += 7
        hits.append("dugaan pelanggaran prosedur")

    if issue_type == "MEDIA_DAN_PERS" and any_phrase(text, ["intimidasi wartawan", "intimidasi jurnalis", "ancam wartawan"]):
        bonus += 8
        hits.append("dugaan intimidasi terhadap pers")

    if issue_type == "KEKERASAN_DAN_KEKUATAN" and any_phrase(text, ["penganiayaan", "penembakan", "penyiksaan", "membunuh", "pembunuhan"]):
        bonus += 12
        hits.append("dugaan kekerasan serius oleh personel")

    if issue_type == "KEJAHATAN_SEKSUAL" and any_phrase(text, ["pemerkosaan", "perkosaan", "pencabulan", "kekerasan seksual"]):
        bonus += 12
        hits.append("dugaan kejahatan seksual terkait personel")

    if issue_type == "PENYALAHGUNAAN_WEWENANG":
        bonus += 7
        hits.append("dugaan penyalahgunaan kewenangan")

    return min(20, bonus), hits


def analyze_article(title, summary="", police_context=True):
    title_text = norm(title)
    context = norm(f"{title} {summary}")

    positive_label, positive_hits = detect_positive(context)
    procedural_label, procedural_hits = detect_procedural_context(context)
    issue_type, issue_subtype, issue_hits = first_issue(context)
    handling_status, handling_hits, handling_points = detect_handling(context)
    role, role_reason = detect_role(context)
    severity, severity_hits = severity_analysis(context, issue_type, role)
    authority, authority_hits = authority_analysis(context)
    relation, relation_hits = relation_analysis(context, role, issue_type)
    impact, impact_hits = impact_analysis(context, role, issue_type)
    evidence, evidence_hits = evidence_analysis(context)
    risk_bonus, risk_hits = context_risk_bonus(context, issue_type, role)

    # Positive classification gets precedence when the sentence clearly says
    # police succeeded/acted, unless the same article explicitly frames police
    # as the subject of misconduct.
    subject_misconduct = role == "SUBJEK_PERMASALAHAN"

    if subject_misconduct:
        sentiment = "negative"
        sentiment_label = "Negatif"
    elif positive_label or procedural_label:
        sentiment = "positive"
        sentiment_label = "Positif"
    elif issue_type != "UMUM" or handling_status == "BELUM_DITANGANI":
        sentiment = "negative"
        sentiment_label = "Negatif"
    elif role == "PENEGAKAN_HUKUM":
        sentiment = "positive"
        sentiment_label = "Positif"
    else:
        sentiment = "neutral"
        sentiment_label = "Netral"

    # Negative issue with unclear relation is deliberately not promoted to high.
    # This is the key distinction the previous engine lacked.
    base = severity + relation + impact + handling_points + evidence + risk_bonus

    # Authority is only a small supporting factor.
    authority_contribution = min(4, max(0, authority - 10))
    score = base + authority_contribution

    routine_enforcement = (
        role == "PENEGAKAN_HUKUM"
        and not subject_misconduct
        and not any_phrase(context, list(RISKY_MISCONDUCT_TERMS))
        and issue_type in {"NARKOBA", "AKTIVITAS_ILEGAL", "KEAMANAN_DAN_KAMTIBMAS", "UMUM"}
    )

    if routine_enforcement:
        # Normal police enforcement is not institutional high attention.
        score = min(score, 35)

    # Strong high-attention floor only when the police/personnel are the
    # subject of the serious misconduct, not when police are the enforcer.
    if subject_misconduct and issue_type in SEVERE_NEGATIVE_ISSUES:
        score = max(score, 70)

    # A serious event by a non-police actor is still negative, but remains
    # middle/low unless there is a separate institutional signal.
    if role == "PENEGAKAN_HUKUM" and severity >= 25:
        score = min(score, 39)

    # Unresolved illegal activity with explicit lack of police response merits
    # at least the middle band, but does not become high by itself.
    if handling_status == "BELUM_DITANGANI" and issue_type == "AKTIVITAS_ILEGAL":
        score = max(score, 40)

    # Ambiguous/insufficiently specified cases should sit in the middle band,
    # not jump to high from a single severe token.
    unclear_subject = (
        issue_type != "UMUM"
        and role not in {"SUBJEK_PERMASALAHAN", "RESPONS_TERHADAP_ISU"}
        and not positive_label
    )
    if unclear_subject and severity >= 20:
        score = min(max(score, 40), 69)

    score = max(0, min(100, int(round(score))))

    # Build concise, explainable evidence.
    reasons = []
    if sentiment_label:
        reasons.append(f"sifat berita: {sentiment_label.lower()}")
    if issue_subtype and issue_type != "UMUM":
        reasons.append(issue_subtype)
    if role_reason:
        reasons.append(role_reason)
    if handling_status == "BELUM_DITANGANI":
        reasons.append("indikasi belum ditangani")
    elif handling_status in {"SEDANG_DITANGANI", "SUDAH_DITANGANI", "SUDAH_DITINDAK"}:
        reasons.append(f"status: {handling_status.lower().replace('_', ' ')}")
    reasons.extend(risk_hits[:2])
    if positive_hits:
        reasons.append("frasa penegakan/hasil positif terdeteksi")

    return {
        "sentiment": sentiment,
        "sentiment_label": sentiment_label,
        "positive_pattern": positive_label,
        "positive_evidence": positive_hits,
        "issue_type": issue_type,
        "issue_subtype": issue_subtype,
        "issue_evidence": issue_hits,
        "polri_relation": role,
        "polri_relation_points": relation,
        "polri_relation_evidence": relation_hits + ([role_reason] if role_reason else []),
        "handling_status": handling_status,
        "handling_evidence": handling_hits,
        "attention_score": score,
        "attention_label": attention_label(score),
        "legacy_priority": legacy_priority(score),
        "attention_components": {
            "severity": severity,
            "polri_relation": relation,
            "authority": authority_contribution,
            "public_impact": impact,
            "handling": handling_points,
            "evidence": evidence,
            "context_risk": risk_bonus,
            "routine_enforcement_cap": 35 if routine_enforcement else None,
        },
        "attention_evidence": {
            "severity": severity_hits,
            "authority": authority_hits,
            "public_impact": impact_hits,
            "evidence": evidence_hits,
            "role": relation_hits,
            "issue": issue_hits,
            "handling": handling_hits,
            "context": risk_hits,
            "positive": positive_hits,
        },
        "attention_reasons": reasons[:8],
    }


def _source_name(article):
    return norm(article.get("source") or article.get("publisher"))


def _case_escalation(articles):
    text = norm(" ".join(a.get("title", "") for a in articles))
    patterns = [
        ("pemeriksaan resmi", ["diperiksa propam", "pemeriksaan propam", "propam periksa", "diperiksa polisi"]),
        ("proses etik", ["proses etik", "sidang etik", "sidang kode etik"]),
        ("tindakan disiplin", ["dipecat", "diberhentikan", "ptdh"]),
        ("proses pidana", ["ditahan", "diproses pidana", "diproses hukum", "divonis"]),
    ]
    hits = []
    points = 0
    for label, terms in patterns:
        if any_phrase(text, terms):
            hits.append(label)
            points += 2
    return min(6, points), hits


def _source_spread(articles):
    sources = {_source_name(a) for a in articles if _source_name(a)}
    count = len(sources)
    if count >= 10:
        return 15, count
    if count >= 7:
        return 12, count
    if count >= 5:
        return 9, count
    if count >= 3:
        return 6, count
    if count >= 2:
        return 3, count
    return 0, count


def case_attention(articles, case=None, active_today=0):
    articles = list(articles or [])
    if not articles:
        return {
            "score": 0,
            "label": "Rendah",
            "priority": "low",
            "breakdown": {},
            "evidence": {},
            "reasons": [],
        }

    analyses = [
        analyze_article(
            article.get("title", ""),
            article.get("summary", ""),
            True,
        )
        for article in articles
    ]

    # Preserve the most serious *institutionally relevant* signal as the case
    # core. Do not let a severe crime handled by police dominate the case.
    subject_analyses = [a for a in analyses if a["polri_relation"] == "SUBJEK_PERMASALAHAN"]
    pool = subject_analyses or [a for a in analyses if a["sentiment"] == "negative"] or analyses
    core = max(pool, key=lambda a: a["attention_score"])

    severity = max(a["attention_components"]["severity"] for a in pool)
    relation = max(a["attention_components"]["polri_relation"] for a in pool)
    authority = max(a["attention_components"]["authority"] for a in pool)
    impact = max(a["attention_components"]["public_impact"] for a in pool)
    handling = max(a["attention_components"]["handling"] for a in pool)
    issue = core

    spread, source_count = _source_spread(articles)
    article_evidence = max(a["attention_components"]["evidence"] for a in analyses)
    corroboration = min(4, max(0, source_count - 1) * 2)
    evidence = min(10, article_evidence + corroboration)

    escalation, escalation_hits = _case_escalation(articles)

    activity = 0
    if active_today >= 1:
        activity = 1
    if active_today >= 2:
        activity = 2
    if active_today >= 4:
        activity = 4
    if active_today >= 7:
        activity = 5

    risk_bonus = max(
        a["attention_components"].get("context_risk", 0)
        for a in pool
    )

    score = severity + relation + impact + handling + evidence + spread + escalation + activity
    score += risk_bonus + authority

    role = core["polri_relation"]
    issue_type = core["issue_type"]

    # Routine enforcement is never made high by volume alone.
    routine_enforcement = (
        role == "PENEGAKAN_HUKUM"
        and not subject_analyses
        and issue_type in {"NARKOBA", "AKTIVITAS_ILEGAL", "KEAMANAN_DAN_KAMTIBMAS", "UMUM"}
        and not any_phrase(
            norm(" ".join(a.get("title", "") for a in articles)),
            list(RISKY_MISCONDUCT_TERMS),
        )
    )
    if routine_enforcement:
        score = min(score, 39)

    # High is reserved for serious institutional/personnel problems.
    if subject_analyses and issue_type in SEVERE_NEGATIVE_ISSUES:
        score = max(score, 70)
    elif subject_analyses and issue_type == "PROFESIONALISME_DAN_PROSEDUR":
        score = max(score, 40)

    if handling == 8 and issue_type == "AKTIVITAS_ILEGAL" and not subject_analyses:
        score = max(score, 40)

    if role == "PENEGAKAN_HUKUM" and not subject_analyses:
        score = min(score, 39)

    score = max(0, min(100, int(round(score))))

    reasons = []
    reasons.extend(issue.get("attention_reasons", [])[:4])
    if spread >= 9:
        reasons.append(f"pemberitaan lintas {source_count} sumber")
    if escalation_hits:
        reasons.extend(escalation_hits[:2])
    if active_today >= 2:
        reasons.append("ada perkembangan pemberitaan hari ini")

    return {
        "score": score,
        "label": attention_label(score),
        "priority": legacy_priority(score),
        "breakdown": {
            "severity": severity,
            "polri_relation": relation,
            "authority_context": authority,
            "public_impact": impact,
            "handling": handling,
            "evidence": evidence,
            "spread": spread,
            "escalation": escalation,
            "current_activity": activity,
            "context_risk": risk_bonus,
        },
        "evidence": {
            "unique_sources": source_count,
            "active_today_articles": active_today,
            "escalation": escalation_hits[:5],
            "issue_type": issue.get("issue_type"),
            "issue_subtype": issue.get("issue_subtype"),
            "sentiment": issue.get("sentiment"),
            "polri_relation": role,
            "handling_status": issue.get("handling_status"),
            "reasons": reasons[:10],
        },
        "reasons": reasons[:10],
    }

# JAGAT_V655_CONTEXT_GUARDRAIL_ACTIVE
# Final semantic guardrail. The base engine remains the primary classifier;
# this layer only resolves known high-value contextual contradictions.
_jagat_v655_base_analyze_article = analyze_article


def _jagat_v655_has(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def _jagat_v655_negated(text, patterns):
    neg = r"(?:tidak|tak|bukan|tanpa)\s+(?:ada\s+)?"
    for pattern in patterns:
        if re.search(r"\b" + neg + pattern, text):
            continue
        if re.search(pattern, text):
            return False
    return True


def _jagat_v655_context_result(result, title, summary):
    text = norm(f"{title} {summary}")

    police_identity = (
        r"\b(?:polisi|polri|polsek|polres|polresta|polrestabes|polda|kapolres|kapolda)\b"
    )
    financial_terms = r"\b(?:pungli|suap|pemerasan|setoran|upeti|tebusan|uang\s+damai|uang\s+pelicin|tangkap\s+lepas|lepas\s+tangkap)\b"

    denial_patterns = [
        r"\btidak\s+ada\s+pungli\b",
        r"\bbukan\s+pungli\b",
        r"\btidak\s+terjadi\s+pungli\b",
        r"\btidak\s+ada\s+setoran\b",
        r"\btidak\s+ada\s+uang\s+damai\b",
        r"\btidak\s+terjadi\s+tangkap\s+lepas\b",
        r"\btidak\s+ada\s+tangkap\s+lepas\b",
    ]
    resolution_patterns = [
        r"\b(?:sudah|telah|resmi)\s+dibayar\b",
        r"\bdibayar\s+\d+\s*(?:x|kali)\s*lipat\b",
        r"\bsepuluh\s+kali\s+lipat\b",
        r"\b(?:ganti\s+rugi|kompensasi|penggantian)\b",
        r"\b(?:klarifikasi|penjelasan)\b.*\b(?:dibayar|diselesaikan|diganti)\b",
    ]
    explicit_misconduct_patterns = [
        r"\boknum\s+(?:polisi|polri)\b.*\b(?:diduga|terlibat|meminta|menerima|memeras|menyalahgunakan)\b",
        r"\b(?:polisi|anggota\s+polisi|anggota\s+polri)\b.*\b(?:diduga\s+meminta|diduga\s+menerima|diduga\s+memeras|diduga\s+melakukan\s+pungli)\b",
        r"\b(?:kapolres|kapolda)\b.*\b(?:diduga|dituduh|terlibat|meminta|menerima)\b",
    ]

    direct_tangkap_lepas = _jagat_v655_has(text, [
        r"\btangkap\s+lepas\b",
        r"\blepas\s+tangkap\b",
    ])
    financial_issue = _jagat_v655_has(text, [financial_terms])
    police_present = re.search(police_identity, text) is not None
    police_station_context = re.search(r"\bpolsek\b|\bpolres\b|\bpolresta\b|\bpolrestabes\b|\bpolda\b", text) is not None
    claimed_police = _jagat_v655_has(text, [
        r"\bmengaku\s+(?:anggota\s+)?(?:polda|polres|polisi|polri)\b",
        r"\bmengaku\s+dari\s+(?:polda|polres|polisi|polri)\b",
    ])
    explicit_misconduct = _jagat_v655_has(text, explicit_misconduct_patterns)
    denied = _jagat_v655_has(text, denial_patterns)
    resolution = _jagat_v655_has(text, resolution_patterns)

    # Strong resolution/denial beats isolated financial keywords unless the
    # same text still explicitly accuses a police actor of misconduct.
    if (denied or resolution) and not explicit_misconduct:
        if result.get("sentiment") != "positive" or result.get("issue_type") != "UMUM":
            result["sentiment"] = "positive"
            result["sentiment_label"] = "Positif"
            result["issue_type"] = "UMUM"
            result["issue_subtype"] = "Pemulihan / Klarifikasi"
            result["issue_evidence"] = []
            result["legacy_priority"] = "low"
            result["attention_score"] = min(int(result.get("attention_score") or 0), 35)
            result["attention_label"] = attention_label(result["attention_score"])
            result["positive_pattern"] = result.get("positive_pattern") or "Pemulihan / klarifikasi"
            result["attention_reasons"] = [
                "konteks utama berupa klarifikasi/pemulihan",
                "tidak ditemukan tuduhan eksplisit yang tetap diarahkan kepada personel",
            ]
        return result

    # Explicit allegation of integrity abuse should never fall back to neutral
    # merely because there is no exact 'polisi diduga' phrase.
    direct_negative = (
        (direct_tangkap_lepas and (police_station_context or police_present))
        or (financial_issue and police_present and (
            _jagat_v655_has(text, [
                r"\b(?:dugaan|diduga|mencuat|diminta|meminta|menerima|bayar|dibayar|setoran|uang|rp\b|juta\b|ribu\b)\b"
            ])
        ))
        or (claimed_police and financial_issue)
    ) and not denied

    if direct_negative:
        result["sentiment"] = "negative"
        result["sentiment_label"] = "Negatif"
        result["issue_type"] = "INTEGRITAS_DAN_KEUANGAN"
        if claimed_police and not explicit_misconduct:
            result["issue_subtype"] = "Dugaan Setoran / Mengatasnamakan Polri"
            result["polri_relation"] = "DUGAAN_MENGATASNAMAKAN_POLRI"
            score_floor = 50
        elif direct_tangkap_lepas and not explicit_misconduct:
            result["issue_subtype"] = "Dugaan Tangkap Lepas / Imbalan"
            result["polri_relation"] = "SUBJEK_PERMASALAHAN"
            score_floor = 55
        else:
            result["issue_subtype"] = "Pungli / Suap / Pemerasan"
            result["polri_relation"] = "SUBJEK_PERMASALAHAN"
            score_floor = 70
        result["issue_evidence"] = [
            x for x in [
                "tangkap lepas" if direct_tangkap_lepas else None,
                "setoran" if has(text, "setoran") else None,
                "pungli" if has(text, "pungli") else None,
                "mengatasnamakan Polri" if claimed_police else None,
            ] if x
        ][:5]
        result["attention_score"] = max(int(result.get("attention_score") or 0), score_floor)
        result["attention_score"] = min(100, result["attention_score"])
        result["attention_label"] = attention_label(result["attention_score"])
        result["legacy_priority"] = legacy_priority(result["attention_score"])
        result["positive_pattern"] = None
        result["positive_evidence"] = []
        result["attention_reasons"] = [
            "indikasi pelanggaran integritas/keuangan terdeteksi secara kontekstual",
            "kata kunci dibaca bersama konteks dugaan, aktor, dan/atau lokasi Polri",
        ]
        return result

    # If the article is clearly a routine police action, keep it positive even
    # if the crime itself contains severe words.
    routine_action = result.get("polri_relation") == "PENEGAKAN_HUKUM" and not explicit_misconduct
    if routine_action and result.get("sentiment") == "negative" and not financial_issue:
        if _jagat_v655_has(text, [
            r"\b(?:berhasil|langsung|berhasil\s+diamankan|diamankan|ditangkap|diungkap)\b",
            r"\bpolisi\b.*\b(?:menangkap|mengamankan|mengungkap|menyita)\b",
        ]):
            result["sentiment"] = "positive"
            result["sentiment_label"] = "Positif"
            result["legacy_priority"] = legacy_priority(int(result.get("attention_score") or 0))

    return result


def analyze_article(title, summary="", police_context=True):
    result = _jagat_v655_base_analyze_article(title, summary, police_context)
    return _jagat_v655_context_result(result, title, summary)

# JAGAT_V656_FINAL_SEMANTIC_CORRECTION
_jagat_v656_base_analyze_article = analyze_article


def _jagat_v656_has(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def _jagat_v656_result(result, title, summary):
    text = norm(f"{title} {summary}")

    # A serious crime described as a crime/incident is still a negative news
    # item for JAGAT even when police are the party handling it. This is not the
    # same as praising the police for a successful arrest.
    crime_terms = [
        r"\bpencabulan\b", r"\bpemerkosaan\b", r"\bperkosaan\b",
        r"\bpembunuhan\b", r"\bpenganiayaan\b", r"\bpenyiksaan\b",
        r"\bpenembakan\b", r"\bkekerasan\b", r"\btewas\b",
        r"\bkorban\b",
    ]
    explicit_positive_enforcement = _jagat_v656_has(text, [
        r"\b(?:berhasil|sukses)\b.{0,80}\b(?:ungkap|mengungkap|tangkap|menangkap|amankan|mengamankan|sita|menyita)\b",
        r"\bpolisi\b.{0,80}\b(?:berhasil|sukses)\b.{0,50}\b(?:ungkap|tangkap|amankan|sita)\b",
    ])

    if (
        result.get("polri_relation") == "PENEGAKAN_HUKUM"
        and result.get("issue_type") != "UMUM"
        and _jagat_v656_has(text, crime_terms)
        and not explicit_positive_enforcement
    ):
        result["sentiment"] = "negative"
        result["sentiment_label"] = "Negatif"
        result["positive_pattern"] = None
        result["positive_evidence"] = []
        # Crime by a non-police actor should not automatically become a high
        # institutional issue merely because the article is negative.
        result["attention_score"] = min(int(result.get("attention_score") or 0), 39)
        result["attention_label"] = attention_label(result["attention_score"])
        result["legacy_priority"] = "low"
        reasons = list(result.get("attention_reasons") or [])
        reasons = [r for r in reasons if "sifat berita: positif" not in str(r).lower()]
        reasons.insert(0, "sifat berita: negatif")
        result["attention_reasons"] = reasons[:8]

    return result


def analyze_article(title, summary="", police_context=True):
    result = _jagat_v656_base_analyze_article(title, summary, police_context)
    return _jagat_v656_result(result, title, summary)

# JAGAT_V657_CRIME_SEMANTIC_FALLBACK
_jagat_v657_base_analyze_article = analyze_article


def _jagat_v657_has(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def _jagat_v657_result(result, title, summary):
    text = norm(f"{title} {summary}")

    police_ref = [
        r"\bpolisi\b", r"\bpolri\b", r"\bpolsek\b", r"\bpolres\b",
        r"\bpolresta\b", r"\bpolrestabes\b", r"\bpolda\b",
        r"\bkapolres\b", r"\bkapolda\b",
    ]
    severe_crimes = [
        ("KEJAHATAN_SEKSUAL", "Kejahatan Seksual", [
            r"\bpencabulan\b", r"\bcabuli\b", r"\bmencabuli\b", r"\bdicabuli\b",
            r"\bpemerkosaan\b", r"\bperkosaan\b",
            r"\bkekerasan\s+seksual\b", r"\bpelecehan\s+seksual\b",
        ]),
        ("KEKERASAN_DAN_KEKUATAN", "Kekerasan / Penggunaan Kekuatan", [
            r"\bpembunuhan\b", r"\bdibunuh\b", r"\bmembunuh\b",
            r"\bpenganiayaan\b", r"\bpenyiksaan\b", r"\bpenembakan\b",
            r"\bditembak\b",
        ]),
    ]

    resolution_context = _jagat_v657_has(text, [
        r"\b(?:tidak|tak|bukan)\s+(?:ada|terjadi)?\s*(?:pungli|suap|pemerasan|setoran|tangkap\s+lepas|lepas\s+tangkap)\b",
        r"\b(?:sudah|telah|resmi)\s+(?:dibayar|diganti|diselesaikan)\b",
        r"\b(?:ganti\s+rugi|kompensasi|penggantian)\b",
    ])
    if resolution_context:
        return result

    if not _jagat_v657_has(text, police_ref):
        return result

    for issue_type, subtype, patterns in severe_crimes:
        if not _jagat_v657_has(text, patterns):
            continue

        if result.get("polri_relation") == "SUBJEK_PERMASALAHAN":
            return result

        result["sentiment"] = "negative"
        result["sentiment_label"] = "Negatif"
        result["issue_type"] = issue_type
        result["issue_subtype"] = subtype
        result["legacy_priority"] = "low"
        result["attention_score"] = min(int(result.get("attention_score") or 0), 39)
        result["attention_label"] = attention_label(result["attention_score"])
        result["positive_pattern"] = None
        result["positive_evidence"] = []
        reasons = list(result.get("attention_reasons") or [])
        reasons = [r for r in reasons if "sifat berita: positif" not in str(r).lower()]
        reasons.insert(0, "sifat berita: negatif")
        result["attention_reasons"] = reasons[:8]
        return result

    return result


def analyze_article(title, summary="", police_context=True):
    result = _jagat_v657_base_analyze_article(title, summary, police_context)
    return _jagat_v657_result(result, title, summary)


