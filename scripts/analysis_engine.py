"""JAGAT V6.5.2 deterministic article/case attention engine.

Design goals:
- Three stable operational attention levels: Rendah, Sedang, Tinggi.
- A 0-100 score remains available for ranking and explanation.
- Keyword hits are evidence, not the priority by themselves.
- Police as enforcer is not treated as police misconduct.
- Police-as-subject, public impact, handling status, corroboration and spread
  are evaluated separately.
"""
import re

ATTENTION_BANDS = [
    (0, 39, "Rendah"),
    (40, 69, "Sedang"),
    (70, 100, "Tinggi"),
]

# ---------------------------------------------------------------------------
# Issue taxonomy. The first matching family is the primary issue group.
# ---------------------------------------------------------------------------
ISSUE_PATTERNS = [
    ("INTEGRITAS_DAN_KEUANGAN", "Pungli / Suap / Pemerasan", [
        "pungli", "pungutan liar", "suap", "gratifikasi", "pemerasan",
        "memeras", "setoran", "upeti", "uang damai", "tarif bayangan",
        "minta uang", "minta bayaran", "sogokan", "transaksi uang",
    ]),
    ("PENYALAHGUNAAN_WEWENANG", "Penyalahgunaan Wewenang", [
        "penyalahgunaan wewenang", "menyalahgunakan wewenang",
        "salahgunakan wewenang", "kriminalisasi", "intervensi",
        "sewenang-wenang", "dibeking", "dibeckup", "backing",
        "tebang pilih", "kebal hukum", "bermain perkara", "tutupi laporan",
        "tutupi laporan orang hilang", "menutupi laporan", "menutup laporan",
        "mengabaikan laporan", "menghapus laporan", "memanipulasi laporan",
    ]),
    ("PROFESIONALISME_DAN_PROSEDUR", "Pelanggaran SOP / Prosedur", [
        "langgar sop", "melanggar sop", "pelanggaran sop", "tak sesuai sop",
        "tidak sesuai sop", "sop penangkapan", "prosedur cacat", "salah prosedur",
        "salah tangkap", "ketidakprofesionalan", "tidak profesional",
        "maladministrasi", "prosedur penangkapan", "prosedur penyidikan",
    ]),
    ("KEKERASAN_DAN_KEKUATAN", "Kekerasan / Penggunaan Kekuatan", [
        "penganiayaan", "kekerasan", "pemukulan", "penyiksaan",
        "penembakan", "menembak", "kekerasan fisik", "penggunaan senjata",
        "tembakan", "ditembak", "dikeroyok",
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
    ("KESEHATAN_REPRODUKSI", "Aborsi / Dugaan Pemaksaan Kehamilan", [
        "aborsi", "menggugurkan", "gugurkan kandungan", "gugur kandungan",
        "memaksa aborsi", "perintah aborsi", "menggugurkan kandungan",
    ]),
    ("NARKOBA", "Narkoba / Narkotika", [
        "narkoba", "narkotika", "sabu", "ganja", "ekstasi", "obat terlarang",
    ]),
    ("AKTIVITAS_ILEGAL", "Aktivitas Ilegal / Dugaan Pembiaran", [
        "tambang ilegal", "galian c ilegal", "galian c", "judi online", "judol",
        "sabung ayam", "rokok ilegal", "solar subsidi", "bbm subsidi", "miras",
        "minuman keras", "aktivitas ilegal", "pembiaran", "kebal razia",
        "ilegal", "barang bukti hilang",
    ]),
    ("MEDIA_DAN_PERS", "Intimidasi / Hambatan terhadap Pers", [
        "intimidasi wartawan", "intimidasi jurnalis", "wartawan diintimidasi",
        "ancam wartawan", "ancaman terhadap wartawan", "halangi peliputan",
        "menghalangi peliputan", "blokir wartawan", "tekanan media",
        "pers dipersulit", "jurnalis diintimidasi",
    ]),
    ("KEAMANAN_DAN_KAMTIBMAS", "Gangguan Keamanan / Kamtibmas", [
        "demo ricuh", "demonstrasi ricuh", "kerusuhan", "bentrok", "tawuran",
        "massa menyerang", "pos polisi dibakar", "mako diserang",
        "markas polisi diserang", "molotov", "huru-hara", "ricuh",
        "penyerangan kantor polisi",
    ]),
    ("DISIPLIN_DAN_LAYANAN", "Disiplin / Layanan", [
        "pelanggaran disiplin", "calo sim", "jalur belakang sim", "pungli samsat",
        "jual beli stck", "pelayanan buruk", "keluhan polisi",
        "pelayanan polisi dikeluhkan", "lalai", "kelalaian",
    ]),
]

# ---------------------------------------------------------------------------
# Handling/status patterns. "BELUM_DITANGANI" is a signal of unresolvedness,
# not a finding of negligence.
# ---------------------------------------------------------------------------
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
        "dalam proses hukum", "ditindaklanjuti",
    ]),
    ("SUDAH_DITANGANI", [
        "sudah ditangani", "telah ditangani", "sudah diproses",
        "telah diproses", "sudah ditindaklanjuti", "telah ditindaklanjuti",
        "sudah ditindak", "berhasil ditangani",
    ]),
    ("SUDAH_DITINDAK", [
        "ditahan", "ditetapkan sebagai tersangka", "tersangka",
        "disidangkan", "sidang etik", "dipecat", "diberhentikan", "ptdh",
        "diproses pidana", "diproses hukum", "divonis",
    ]),
]

# ---------------------------------------------------------------------------
# Strong semantic signals. These are grouped so one article does not receive
# points repeatedly just because many synonyms appear.
# ---------------------------------------------------------------------------
SEVERITY_BY_ISSUE = {
    "INTEGRITAS_DAN_KEUANGAN": 24,
    "PENYALAHGUNAAN_WEWENANG": 23,
    "PROFESIONALISME_DAN_PROSEDUR": 15,
    "KEKERASAN_DAN_KEKUATAN": 26,
    "KEJAHATAN_SEKSUAL": 29,
    "ETIK_DAN_PERILAKU": 12,
    "NARKOBA": 12,
    "AKTIVITAS_ILEGAL": 14,
    "MEDIA_DAN_PERS": 24,
    "KEAMANAN_DAN_KAMTIBMAS": 21,
    "DISIPLIN_DAN_LAYANAN": 9,
    "KESEHATAN_REPRODUKSI": 16,
    "UMUM": 3,
}

CRITICAL_TERMS = {
    "pembunuhan": 30,
    "tewas": 28,
    "meninggal": 27,
    "pemerkosaan": 30,
    "perkosaan": 30,
    "kekerasan seksual": 30,
    "pencabulan anak": 30,
    "penyiksaan": 28,
    "mako diserang": 28,
    "pos polisi dibakar": 28,
    "penembakan": 27,
    "korupsi": 27,
}

AUTHORITY_PATTERNS = [
    (20, ["kapolda", "kapolres", "pju", "pejabat utama", "perwira tinggi"]),
    (17, ["kombes", "akbp", "kompol", "perwira"]),
    (14, ["kasat", "kepala satuan", "resnarkoba", "reskrim", "satres", "satlantas", "propam"]),
    (10, ["anggota polisi", "anggota polri", "oknum polisi", "oknum polri"]),
]

IMPACT_PATTERNS = [
    (20, ["wartawan", "jurnalis", "anak", "korban jiwa", "masyarakat luas"]),
    (18, ["kepercayaan publik", "kepercayaan masyarakat", "pelayanan publik", "ketertiban umum"]),
    (14, ["warga", "masyarakat", "pengaduan", "laporan", "kerugian"]),
    (10, ["korban", "perempuan", "media", "pers"]),
]

ROLE_PATTERNS = {
    "SUBJEK_PERMASALAHAN": [
        r"\boknum (?:polisi|polri)\b",
        r"\banggota(?:\s+[^,;:-]{0,60})?\bpol(?:isi|ri)\b.{0,120}\b(?:diduga|terlibat|tersangka|melanggar|melakukan|ditangkap|ditahan)\b",
        r"\banggota\s+(?:resnarkoba|reskrim|satres|satlantas|propam)\b.{0,120}\b(?:diduga|terlibat|tersangka|melanggar|melakukan|ditangkap|ditahan)\b",
        r"\b(?:perwira|kapolres|kapolda|pju|kompol|akbp|kombes)\b.{0,120}\b(?:diduga|terlibat|melanggar|melakukan|tersangka)\b",
        r"\bpolisi\b.{0,100}\b(?:diduga|terlibat|melanggar|melakukan)\b",
    ],
    "KORBAN": [
        r"\bpolisi\b.{0,60}\b(?:ditembak|tertembak|diserang|dianiaya|dikeroyok|terluka|tewas|meninggal)\b",
        r"\bpolisi\b.{0,80}\b(?:menjadi korban|jadi korban|sebagai korban)\b",
    ],
    "PENEGAKAN_HUKUM": [
        r"\bpolisi\b.{0,70}\b(?:tangkap|menangkap|mengamankan|amankan|ungkap|mengungkap|sita|menyita|menggagalkan|gagalkan|membekuk|meringkus|gerebek|menggerebek|menemukan|temukan|menahan|menetapkan|memproses|menindak)\b",
        r"\b(?:polres|polresta|polrestabes)\b.{0,90}\b(?:ungkap|amankan|sita|tangkap|gagalkan|tahan|proses|tindak)\b",
    ],
    "RESPONS_TERHADAP_ISU": [
        r"\b(?:polisi|polres|propam|polda)\b.{0,100}\b(?:menangani|tanggapi|menindaklanjuti|memeriksa|menyelidiki|mendalami)\b",
        r"\b(?:belum tersentuh|belum ditangani|belum ada tindakan|belum ada respons|tak kunjung ditangani|tidak ditanggapi|tidak digubris|dibiarkan|didiamkan)\b.{0,80}\bpolisi\b",
        r"\bpolisi\b.{0,80}\b(?:belum tersentuh|belum ditangani|belum ada tindakan|belum ada respons|tak kunjung ditangani|tidak ditanggapi|tidak digubris)\b",
        r"\b(?:belum tersentuh|belum ditangani|belum ada tindakan|belum ada respons|tak kunjung ditangani|tidak ditanggapi|tidak digubris)\b.{0,80}\bpolisi\b",
    ],
}

ESCALATION_PATTERNS = [
    ("pemeriksaan resmi", ["diperiksa propam", "pemeriksaan propam", "propam periksa", "diperiksa polisi"]),
    ("proses etik", ["proses etik", "sidang etik", "sidang kode etik"]),
    ("tindakan disiplin", ["dipecat", "diberhentikan", "ptdh"]),
    ("proses pidana", ["tersangka", "ditahan", "diproses pidana", "diproses hukum"]),
]


def norm(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has(text, phrase):
    return re.search(
        r"(?<![a-z0-9])" + re.escape(norm(phrase)) + r"(?![a-z0-9])",
        norm(text),
    ) is not None


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


def detect_role(text):
    for role in ("SUBJEK_PERMASALAHAN", "KORBAN", "RESPONS_TERHADAP_ISU", "PENEGAKAN_HUKUM"):
        for pattern in ROLE_PATTERNS[role]:
            if re.search(pattern, text):
                return role
    return "INFORMASI_UMUM"


def issue_analysis(text):
    if has(text, "wartawan") and any(
        has(text, x) for x in ("intimidasi", "ancam", "ancaman", "tekanan", "halangi peliputan", "dihalangi")
    ):
        hits = [x for x in ("wartawan", "intimidasi", "ancam", "ancaman", "halangi peliputan") if has(text, x)]
        return "MEDIA_DAN_PERS", "Intimidasi / Hambatan terhadap Pers", hits[:4]
    for issue_type, subtype, terms in ISSUE_PATTERNS:
        hits = [term for term in terms if has(text, term)]
        if hits:
            return issue_type, subtype, hits[:4]
    return "UMUM", "Belum Teridentifikasi", []


def handling_analysis(text):
    for status, terms in HANDLING_PATTERNS:
        hits = [term for term in terms if has(text, term)]
        if hits:
            if status == "BELUM_DITANGANI":
                points = 5
            elif status == "SEDANG_DITANGANI":
                points = 3
            elif status == "SUDAH_DITINDAK":
                points = 2
            else:
                points = 1
            return status, hits[:3], points
    return "BELUM_ADA_INFORMASI", [], 0


def best_match(text, patterns):
    for points, terms in patterns:
        hits = [term for term in terms if has(text, term)]
        if hits:
            return points, hits[:4]
    return 0, []


def severity_analysis(text, issue_type):
    critical_hits = [term for term in CRITICAL_TERMS if has(text, term)]
    if critical_hits:
        return max(CRITICAL_TERMS[t] for t in critical_hits), critical_hits[:4]

    base = SEVERITY_BY_ISSUE.get(issue_type, 3)
    modifiers = []
    if has(text, "serius"):
        modifiers.append(2)
    if has(text, "berulang") or has(text, "lagi"):
        modifiers.append(2)
    if has(text, "tangkap lepas"):
        base = max(base, 18)
    if issue_type == "PROFESIONALISME_DAN_PROSEDUR" and has(text, "langgar sop"):
        base = max(base, 15)
    return min(30, base + sum(modifiers[:2])), []


def impact_analysis(text, role, issue_type):
    points, hits = best_match(text, IMPACT_PATTERNS)
    if issue_type in {"KEJAHATAN_SEKSUAL", "KESEHATAN_REPRODUKSI"} and any(has(text, x) for x in ("murid", "siswa", "pelajar", "anak", "usia 8", "usia 9", "usia 10", "tahun")):
        points = max(points, 18)
    if role == "SUBJEK_PERMASALAHAN" and points < 10:
        points = 10
    if role == "PENEGAKAN_HUKUM" and points > 12:
        points = min(points, 12)
    return min(20, points), hits


def relation_analysis(text, issue_type, role):
    if role == "SUBJEK_PERMASALAHAN":
        points = 16
        if any(has(text, x) for x in ("pungli", "suap", "pemerasan", "penyalahgunaan wewenang", "intimidasi wartawan")):
            points = 20
        elif any(has(text, x) for x in ("perwira", "pju", "kapolres", "kapolda", "kompol", "akbp", "kombes")):
            points = 18
        return points, ["polisi sebagai subjek permasalahan"]
    if role == "KORBAN":
        return 10, ["polisi sebagai korban"]
    if role == "RESPONS_TERHADAP_ISU":
        return 8, ["terdapat isu terkait respons penanganan Polri"]
    if role == "PENEGAKAN_HUKUM":
        return 5, ["Polri sebagai penindak"]
    return 0, []


def article_evidence_score(title, text):
    if not title:
        return 0, []
    score = 2
    hits = []
    for label, terms, points in [
        ("klarifikasi/tanggapan", ["klarifikasi", "menanggapi", "kata polisi", "ujar polisi"], 2),
        ("tindak lanjut resmi", ["propam", "diperiksa", "penyelidikan", "penyidikan", "sidang etik"], 2),
    ]:
        if any(has(text, term) for term in terms):
            score += points
            hits.append(label)
    return min(6, score), hits


def analyze_article(title, summary="", police_context=True):
    title_text = norm(title)
    context = norm(f"{title} {summary}")
    issue_type, issue_subtype, issue_hits = issue_analysis(context)
    handling_status, handling_hits, handling_points = handling_analysis(context)
    role = detect_role(context)

    severity, severity_hits = severity_analysis(context, issue_type)
    authority, authority_hits = best_match(context, AUTHORITY_PATTERNS)
    relation, relation_hits = relation_analysis(context, issue_type, role)
    impact, impact_hits = impact_analysis(context, role, issue_type)
    evidence, evidence_hits = article_evidence_score(title_text, context)

    if not police_context and role == "INFORMASI_UMUM":
        authority = 0
        relation = 0

    # Routine enforcement should not be promoted simply by high word counts.
    routine_enforcement = (
        role == "PENEGAKAN_HUKUM"
        and issue_type in {"NARKOBA", "UMUM", "AKTIVITAS_ILEGAL"}
        and handling_status in {"SUDAH_DITANGANI", "SUDAH_DITINDAK", "BELUM_ADA_INFORMASI"}
        and not any(has(context, x) for x in ("diduga", "langgar sop", "penyalahgunaan wewenang", "intimidasi", "pungli", "suap", "pemerasan"))
    )

    preliminary = severity + relation + impact + handling_points + evidence
    if routine_enforcement:
        preliminary = min(preliminary, 32)

    return {
        "issue_type": issue_type,
        "issue_subtype": issue_subtype,
        "issue_evidence": issue_hits,
        "polri_relation": role,
        "polri_relation_points": relation,
        "polri_relation_evidence": relation_hits,
        "handling_status": handling_status,
        "handling_evidence": handling_hits,
        "attention_score": int(min(100, preliminary)),
        "attention_label": attention_label(preliminary),
        "legacy_priority": legacy_priority(preliminary),
        "attention_components": {
            "severity": severity,
            "polri_relation": relation,
            "authority": authority,
            "public_impact": impact,
            "handling": handling_points,
            "evidence": evidence,
            "routine_enforcement_cap": 32 if routine_enforcement else None,
        },
        "attention_evidence": {
            "severity": severity_hits,
            "authority": authority_hits,
            "public_impact": impact_hits,
            "evidence": evidence_hits,
            "role": relation_hits,
            "issue": issue_hits,
            "handling": handling_hits,
        },
    }


def _source_name(article):
    return norm(article.get("source") or article.get("publisher"))


def _case_escalation(articles):
    text = norm(" ".join(a.get("title", "") for a in articles))
    hits = []
    points = 0
    for label, terms in ESCALATION_PATTERNS:
        if any(has(text, term) for term in terms):
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

    # The highest substantive signal defines the incident's core risk.
    severity = max(a["attention_components"]["severity"] for a in analyses)
    relation = max(a["attention_components"]["polri_relation"] for a in analyses)
    authority = max(a["attention_components"]["authority"] for a in analyses)
    impact = max(a["attention_components"]["public_impact"] for a in analyses)
    handling = max(a["attention_components"]["handling"] for a in analyses)
    issue = max(analyses, key=lambda a: a["attention_components"]["severity"])

    # Corroboration: distinct sources add confidence but are capped.
    spread, source_count = _source_spread(articles)
    article_evidence = max(
        a["attention_components"]["evidence"]
        for a in analyses
    )
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

    # Authority is supporting context, not an extra severity dimension.
    authority_contribution = min(6, max(0, authority - 10))

    score = severity + relation + impact + handling + evidence + spread + escalation + activity + authority_contribution

    role = issue.get("polri_relation", "INFORMASI_UMUM")
    issue_type = issue.get("issue_type", "UMUM")
    # Routine police enforcement is deliberately capped unless a misconduct
    # signal changes the semantic role of the story.
    all_text = norm(" ".join(a.get("title", "") for a in articles))
    routine_enforcement = (
        role == "PENEGAKAN_HUKUM"
        and issue_type in {"NARKOBA", "UMUM", "AKTIVITAS_ILEGAL"}
        and not any(has(all_text, x) for x in (
            "diduga", "langgar sop", "pelanggaran sop", "penyalahgunaan wewenang",
            "pungli", "suap", "pemerasan", "intimidasi", "dibiarkan",
            "belum tersentuh", "belum ditangani",
        ))
    )
    if routine_enforcement:
        score = min(score, 39)

    # Floor rules prevent important semantic incidents from remaining low
    # merely because they have one source.
    if role == "SUBJEK_PERMASALAHAN" and severity >= 15:
        score = max(score, 40)
    if issue_type == "MEDIA_DAN_PERS" and role == "SUBJEK_PERMASALAHAN":
        score = max(score, 60)
    if issue_type == "KEJAHATAN_SEKSUAL" and role == "SUBJEK_PERMASALAHAN":
        score = max(score, 60)
    if handling == 5 and issue_type == "AKTIVITAS_ILEGAL":
        score = max(score, 40)
    if severity >= 27:
        score = max(score, 70)

    score = int(min(100, score))

    reasons = []
    if issue.get("issue_subtype"):
        reasons.append(issue["issue_subtype"])
    if role == "SUBJEK_PERMASALAHAN":
        reasons.append("Polri/personel menjadi subjek permasalahan")
    elif role == "PENEGAKAN_HUKUM":
        reasons.append("Polri sebagai pihak penindak")
    elif role == "KORBAN":
        reasons.append("Polisi sebagai korban")
    if handling == 5:
        reasons.append("indikasi belum ditangani")
    elif handling == 3:
        reasons.append("sedang dalam penanganan")
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
            "authority_context": authority_contribution,
            "public_impact": impact,
            "handling": handling,
            "evidence": evidence,
            "spread": spread,
            "escalation": escalation,
            "current_activity": activity,
        },
        "evidence": {
            "unique_sources": source_count,
            "active_today_articles": active_today,
            "escalation": escalation_hits[:5],
            "issue_type": issue.get("issue_type"),
            "issue_subtype": issue.get("issue_subtype"),
            "polri_relation": role,
            "handling_status": issue.get("handling_status"),
            "reasons": reasons[:8],
        },
        "reasons": reasons[:8],
    }
