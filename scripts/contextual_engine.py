"""JAGAT contextual classification layer.

Purpose:
- separate Polri misconduct from normal law-enforcement activity;
- understand negation/denial/allegation phrases;
- classify from title + summary, not title-only;
- attach explainable evidence without external AI dependencies.
"""

import re

from analysis_engine import analyze_article


def norm(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def has_phrase(text, phrase):
    text = norm(text)
    phrase = norm(phrase)
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text) is not None


def any_phrase(text, phrases):
    return any(has_phrase(text, p) for p in phrases)


DENIAL_PATTERNS = [
    r"\b(?:membantah|menyangkal|menepis|bantah|tepis|dibantah|disangkal|tidak benar|tak benar|tidak terlibat|tak terlibat)\b",
    r"\b(?:membantah|menyangkal|menepis)\b.{0,100}\b(?:tuduhan|dugaan|isu|kabar)\b",
]

ALLEGATION_PATTERNS = [
    r"\b(?:diduga|dituduh|disinyalir|dicurigai|terindikasi|dilaporkan|dituding)\b",
]

ENFORCEMENT_PATTERNS = [
    r"\b(?:polisi|polri|polda|polres|polresta|polrestabes|polsek)\b.{0,90}\b(?:berhasil|sukses|menangkap|tangkap|diamankan|mengamankan|amankan|mengungkap|ungkap|menggagalkan|gagalkan|menyita|sita|menindak|tindak|menahan|menetapkan|memproses)\b",
    r"\b(?:pelaku|tersangka|pengedar|bandar|penjahat)\b.{0,80}\b(?:ditangkap|diamankan|ditahan)\b.{0,80}\b(?:polisi|polri|polres|polda|polsek)\b",
]

POLRI_SUBJECT_PATTERNS = [
    r"\b(?:oknum|anggota|personel|perwira|kapolres|kapolda|pju)\b.{0,80}\b(?:polisi|polri)?\b.{0,100}\b(?:diduga|dituduh|terlibat|melanggar|melakukan|meminta|menerima|menembak|menganiaya|mengintimidasi|memeras|menyalahgunakan)\b",
    r"\b(?:polisi|polri)\b.{0,70}\b(?:diduga|dituduh|terlibat|melanggar|melakukan|meminta|menerima|menembak|menganiaya|mengintimidasi|memeras|menyalahgunakan)\b",
]

VICTIM_PATTERNS = [
    r"\b(?:polisi|polri|anggota polisi|anggota polri)\b.{0,50}\b(?:menjadi korban|jadi korban|ditembak|dibacok|diserang|dianiaya)\b",
]

SERVICE_NEGATIVE = [
    "pelayanan buruk", "keluhan polisi", "protes terhadap polisi", "polisi dilaporkan",
    "polisi diduga lalai", "kelalaian polisi", "kritik polisi", "pelayanan polisi dikeluhkan",
    "layanan polisi dikeluhkan", "warga mengeluh", "warga mengeluhkan", "warga keluhkan",
    "keluhkan pelayanan polisi", "keluhan layanan polisi",
]

POSITIVE_ENFORCEMENT_TERMS = [
    "berhasil menangkap", "berhasil mengungkap", "berhasil mengamankan", "berhasil menggagalkan",
    "mengungkap kasus", "ungkap kasus", "menangkap pelaku", "mengamankan tersangka",
    "sita barang bukti", "menyita barang bukti", "gagalkan aksi",
]

MISCONDUCT_TERMS = [
    "pungli", "pungutan liar", "suap", "gratifikasi", "pemerasan", "memeras", "penyalahgunaan wewenang",
    "dibeking", "dibeckup", "backing", "kriminalisasi", "salah prosedur", "melanggar sop",
    "penganiayaan", "penyiksaan", "penembakan", "pencabulan", "pemerkosaan", "intimidasi wartawan",
    "perselingkuhan", "aborsi paksa", "narkoba", "korupsi",
]


def regex_any(text, patterns):
    text = norm(text)
    return any(re.search(p, text) for p in patterns)


def detect_assertion(text):
    text = norm(text)
    denial = [p for p in DENIAL_PATTERNS if re.search(p, text)]
    allegation = [p for p in ALLEGATION_PATTERNS if re.search(p, text)]
    if denial:
        return "DENIAL", min(95, 70 + len(denial) * 10), ["terdapat frasa bantahan/penyangkalan"]
    if allegation:
        return "ALLEGATION", min(90, 65 + len(allegation) * 8), ["terdapat frasa dugaan/tuduhan"]
    return "FACTUAL", 75, []


def contextualize(title, summary=""):
    title = str(title or "").strip()
    summary = str(summary or "").strip()
    text = norm(f"{title} {summary}")

    base = analyze_article(title, summary, police_context=True)
    assertion, assertion_confidence, assertion_evidence = detect_assertion(text)

    explicit_subject = regex_any(text, POLRI_SUBJECT_PATTERNS) or any_phrase(text, [
        "oknum polisi", "oknum polri", "anggota polisi", "anggota polri", "personel polri"
    ])
    explicit_enforcer = regex_any(text, ENFORCEMENT_PATTERNS)
    police_victim = regex_any(text, VICTIM_PATTERNS)
    service_negative = any_phrase(text, SERVICE_NEGATIVE)
    misconduct = any_phrase(text, MISCONDUCT_TERMS)
    direct_positive = any_phrase(text, POSITIVE_ENFORCEMENT_TERMS)

    relation = base.get("polri_relation") or "INFORMASI_UMUM"
    relation_reason = list(base.get("polri_relation_evidence") or [])

    if explicit_enforcer and not explicit_subject:
        relation = "PENEGAKAN_HUKUM"
        relation_reason = ["Polri berperan sebagai pihak penindak"]
    elif police_victim:
        relation = "KORBAN"
        relation_reason = ["Polri/personel terdeteksi sebagai korban peristiwa"]
    elif explicit_subject:
        relation = "SUBJEK_PERMASALAHAN"
        relation_reason = ["Polri/personel menjadi subjek masalah"]

    issue_type = base.get("issue_type", "UMUM")
    issue_subtype = base.get("issue_subtype", "Informasi Umum")
    scope = "neutral"

    if assertion == "DENIAL" and not any_phrase(text, ["diperiksa propam", "ditahan", "ditetapkan sebagai tersangka", "dipecat", "sidang etik", "terbukti"]):
        sentiment = "neutral"
        sentiment_label = "Netral"
        scope = "neutral"
        category = "NETRAL / BANTAHAN / KLARIFIKASI"
        score = min(int(base.get("attention_score", 0)), 39)
        reason = ["frasa dugaan dibarengi bantahan/penyangkalan", "bantahan diprioritaskan sampai ada bukti tindak lanjut yang lebih kuat"]
    elif relation == "SUBJEK_PERMASALAHAN" and misconduct:
        sentiment = "negative"
        sentiment_label = "Negatif"
        scope = "negative"
        category = "NEGATIF - " + str(issue_subtype).upper()
        score = int(base.get("attention_score", 0))
        reason = ["Polri/personel menjadi subjek permasalahan", str(issue_subtype)]
    elif relation == "PENEGAKAN_HUKUM" and (explicit_enforcer or direct_positive):
        sentiment = "positive"
        sentiment_label = "Positif"
        scope = "case"
        category = "UNGKAP KASUS / PENINDAKAN"
        score = min(int(base.get("attention_score", 0)), 39)
        reason = ["Polri berperan sebagai pihak penindak", "tidak ditemukan indikator utama misconduct oleh personel"]
    elif relation == "KORBAN":
        sentiment = "neutral"
        sentiment_label = "Netral"
        scope = "neutral"
        category = "NETRAL / POLRI SEBAGAI KORBAN"
        score = min(int(base.get("attention_score", 0)), 39)
        reason = ["Polri/personel terdeteksi sebagai korban, bukan pelaku"]
    elif service_negative and relation in {"SUBJEK_PERMASALAHAN", "RESPONS_TERHADAP_ISU", "INFORMASI_UMUM"}:
        sentiment = "negative"
        sentiment_label = "Negatif"
        scope = "negative"
        category = "NEGATIF - KINERJA/LAYANAN POLRI"
        score = max(int(base.get("attention_score", 0)), 40)
        reason = ["terdapat keluhan/kritik terkait layanan atau respons Polri"]
    elif issue_type != "UMUM" and relation in {"INFORMASI_UMUM", "KORBAN"}:
        sentiment = "neutral"
        sentiment_label = "Netral"
        scope = "neutral"
        category = "NETRAL / PERISTIWA"
        score = min(int(base.get("attention_score", 0)), 39)
        reason = ["isu/peristiwa ditemukan tetapi relasi Polri sebagai pihak bermasalah tidak cukup kuat"]
    else:
        sentiment = base.get("sentiment", "neutral")
        sentiment_label = base.get("sentiment_label", "Netral")
        scope = "negative" if sentiment == "negative" else "positive" if sentiment == "positive" else "neutral"
        category = base.get("classification_category") or (
            "POSITIF / PENEGAKAN HUKUM" if sentiment == "positive" else
            "NEGATIF - " + str(issue_subtype).upper() if sentiment == "negative" else
            "NETRAL / LAINNYA"
        )
        score = int(base.get("attention_score", 0))
        reason = list(base.get("attention_reasons") or [])[:4]

    if assertion == "ALLEGATION":
        reason.append("status klaim: dugaan/tuduhan")
    elif assertion == "DENIAL":
        reason.append("status klaim: bantahan/penyangkalan")

    return {
        **base,
        "sentiment": sentiment,
        "sentiment_label": sentiment_label,
        "scope": scope,
        "scope_label": {"negative": "Negatif", "case": "Ungkap Kasus", "positive": "Positif", "neutral": "Netral"}.get(scope, "Netral"),
        "classification_category": category,
        "polri_relation": relation,
        "polri_relation_evidence": relation_reason,
        "assertion_status": assertion,
        "assertion_confidence": assertion_confidence,
        "assertion_evidence": assertion_evidence,
        "contextual_attention_score": max(0, min(100, score)),
        "attention_score": max(0, min(100, score)),
        "attention_label": "Tinggi" if score >= 70 else "Sedang" if score >= 40 else "Rendah",
        "contextual_reason": reason[:8],
        "contextual_flags": {
            "explicit_polri_subject": explicit_subject,
            "explicit_polri_enforcer": explicit_enforcer,
            "polri_victim": police_victim,
            "service_negative": service_negative,
            "misconduct_signal": misconduct,
            "direct_positive_enforcement": direct_positive,
        },
    }
