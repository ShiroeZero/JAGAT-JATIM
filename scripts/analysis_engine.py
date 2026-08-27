"""JAGAT V6.5 - unified article/case analysis engine."""
import re

ATTENTION_BANDS = [
    (0, 24, "Rendah"),
    (25, 49, "Perlu Perhatian"),
    (50, 69, "Atensi"),
    (70, 84, "Atensi Tinggi"),
    (85, 100, "Kritis"),
]

HANDLING_PATTERNS = [
    ("BELUM_DITANGANI", [
        "belum tersentuh", "belum ditangani", "belum ditindaklanjuti",
        "belum ada tindakan", "belum ada respons", "tak kunjung ditangani",
        "tidak kunjung ditangani", "tidak ditanggapi", "tidak digubris",
        "dibiarkan", "didiamkan", "laporan diabaikan", "belum diproses",
        "tak kunjung diproses", "belum ada penanganan",
    ]),
    ("SEDANG_DITANGANI", [
        "sedang ditangani", "dalam penanganan", "sedang diperiksa",
        "sedang diselidiki", "tengah diselidiki", "ditangani polisi",
        "ditangani propam", "diproses propam", "sedang diproses",
        "ditindaklanjuti polisi", "didalami polisi", "didalami propam",
    ]),
    ("SUDAH_DITINDAK", [
        "ditahan", "ditetapkan sebagai tersangka", "tersangka",
        "disidangkan", "sidang etik", "dipecat", "diberhentikan", "ptdh",
        "diproses pidana", "diproses hukum", "divonis",
    ]),
    ("SUDAH_DITANGANI", [
        "sudah ditangani", "telah ditangani", "sudah diproses",
        "telah diproses", "sudah ditindaklanjuti", "telah ditindaklanjuti",
        "sudah diamankan", "sudah ditindak", "berhasil ditangani",
    ]),
]

ISSUE_PATTERNS = [
    ("INTEGRITAS_KEUANGAN", "DUGAAN PUNGLI/SUAP/PEMERASAN", [
        "pungli", "pungutan liar", "suap", "gratifikasi", "pemerasan",
        "memeras", "setoran", "upeti", "uang damai", "tarif bayangan",
        "minta uang", "minta bayaran", "sogokan", "transaksi uang",
    ]),
    ("PENYALAHGUNAAN_WEWENANG", "DUGAAN PENYALAHGUNAAN WEWENANG", [
        "penyalahgunaan wewenang", "menyalahgunakan wewenang",
        "salahgunakan wewenang", "kriminalisasi", "intervensi",
        "arogan", "sewenang-wenang", "dibeking", "dibeckup", "backing",
        "tebang pilih", "kebal hukum", "bermain perkara",
    ]),
    ("PELANGGARAN_PROSEDUR", "DUGAAN PELANGGARAN SOP/PROSEDUR", [
        "langgar sop", "melanggar sop", "pelanggaran sop", "tak sesuai sop",
        "tidak sesuai sop", "sop penangkapan", "prosedur cacat", "salah prosedur",
        "salah tangkap", "ketidakprofesionalan", "tidak profesional",
        "maladministrasi", "prosedur penangkapan", "prosedur penyidikan",
    ]),
    ("KEKERASAN_PENGGUNAAN_KEKUATAN", "DUGAAN KEKERASAN/PENGGUNAAN KEKUATAN", [
        "penganiayaan", "kekerasan", "pemukulan", "penyiksaan",
        "penembakan", "menembak", "dibacok", "kekerasan fisik",
        "penggunaan senjata", "tembakan",
    ]),
    ("KEJAHATAN_SEKSUAL", "DUGAAN KEJAHATAN SEKSUAL", [
        "pemerkosaan", "perkosaan", "pencabulan", "cabul",
        "kekerasan seksual", "pelecehan seksual", "eksploitasi seksual",
        "aborsi paksa", "seksual terhadap anak",
    ]),
    ("ETIK_PERSONAL", "DUGAAN PELANGGARAN ETIK/PERILAKU", [
        "perselingkuhan", "selingkuh", "nikah siri", "hubungan gelap",
        "tiduri", "tidur dengan", "asusila", "kdrt", "mabuk",
    ]),
    ("NARKOBA", "DUGAAN KETERLIBATAN NARKOBA", [
        "narkoba", "narkotika", "sabu", "ganja", "ekstasi", "obat terlarang",
    ]),
    ("AKTIVITAS_ILEGAL", "AKTIVITAS ILEGAL / DUGAAN PEMBIARAN", [
        "tambang ilegal", "galian c ilegal", "galian c", "judi online", "judol",
        "sabung ayam", "rokok ilegal", "solar subsidi", "bbm subsidi", "miras",
        "minuman keras", "aktivitas ilegal", "pembiaran", "tidak tersentuh hukum",
        "kebal razia", "ilegal", "barang bukti hilang",
    ]),
    ("MEDIA_INFORMASI", "DUGAAN INTIMIDASI/HAMBATAN TERHADAP PERS", [
        "intimidasi wartawan", "intimidasi jurnalis", "wartawan diintimidasi",
        "ancam wartawan", "ancaman terhadap wartawan", "halangi peliputan",
        "menghalangi peliputan", "blokir wartawan", "tekanan media",
        "pers dipersulit", "jurnalis diintimidasi",
    ]),
    ("KEAMANAN_KAMTIBMAS", "GANGGUAN KEAMANAN/KAMTIBMAS", [
        "demo ricuh", "demonstrasi ricuh", "kerusuhan", "bentrok", "tawuran",
        "massa menyerang", "pos polisi dibakar", "mako diserang",
        "markas polisi diserang", "molotov", "huru-hara", "ricuh",
        "penyerangan kantor polisi",
    ]),
    ("DISIPLIN_LAYANAN", "PELANGGARAN DISIPLIN/LAYANAN", [
        "pelanggaran etik", "pelanggaran disiplin", "calo sim", "jalur belakang sim",
        "pungli samsat", "jual beli stck", "pelayanan buruk", "keluhan polisi",
        "pelayanan polisi dikeluhkan", "lalai", "kelalaian",
    ]),
]

SEVERITY_PATTERNS = [
    (25, ["pembunuhan", "pemerkosaan", "kekerasan seksual", "pos polisi dibakar", "mako diserang", "penembakan"]),
    (22, ["pemerasan", "penyiksaan", "korupsi", "suap", "pungli", "intimidasi wartawan"]),
    (19, ["penyalahgunaan wewenang", "narkoba", "aborsi", "pencabulan", "kekerasan", "tangkap lepas"]),
    (16, ["langgar sop", "melanggar sop", "pelanggaran sop", "salah tangkap", "salah prosedur", "ketidakprofesionalan", "maladministrasi"]),
    (13, ["perselingkuhan", "pelanggaran etik", "pelanggaran disiplin", "tambang ilegal", "judi", "pembiaran"]),
]

AUTHORITY_PATTERNS = [
    (15, ["kapolres", "kapolda", "pju", "pejabat utama"]),
    (12, ["perwira", "kompol", "akbp", "kombes", "iptu", "ipda"]),
    (9, ["resnarkoba", "reskrim", "satres", "satlantas", "propam"]),
    (5, ["anggota polisi", "anggota polri", "oknum polisi", "oknum polri"]),
]

IMPACT_PATTERNS = [
    (20, ["wartawan", "jurnalis", "masyarakat", "publik", "korban", "anak", "perempuan"]),
    (16, ["pelayanan", "penegakan hukum", "kepercayaan publik", "ketertiban umum"]),
    (12, ["warga", "laporan", "pengaduan", "kerugian"]),
    (8, ["diduga", "dipersoalkan", "dikeluhkan"]),
]

ESCALATION_PATTERNS = [
    (5, ["propam periksa", "diperiksa propam", "sidang etik", "dipecat", "diberhentikan", "tersangka", "ditahan"]),
]


def norm(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has(text, phrase):
    text = norm(text)
    phrase = norm(phrase)
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text) is not None


def attention_label(score):
    score = max(0, min(100, int(round(score or 0))))
    for low, high, label in ATTENTION_BANDS:
        if low <= score <= high:
            return label
    return "Kritis"


def legacy_priority(score):
    score = int(round(score or 0))
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _best_reason(text, patterns):
    for points, terms in patterns:
        hits = [term for term in terms if has(text, term)]
        if hits:
            return points, hits
    return 0, []


def handling_analysis(text):
    for status, terms in HANDLING_PATTERNS:
        hits = [term for term in terms if has(text, term)]
        if hits:
            # A reported "not handled" signal is meaningful, but cannot
            # itself assert negligence as fact.
            points = 8 if status == "BELUM_DITANGANI" else 4 if status == "SEDANG_DITANGANI" else 1
            return status, hits[:3], points
    return "BELUM_ADA_INFORMASI", [], 0


def issue_analysis(text):
    # Compound evidence for media/journalist intimidation can appear as
    # "intimidasi dua wartawan" rather than the exact phrase "intimidasi wartawan".
    if has(text, "wartawan") and any(has(text, x) for x in ("intimidasi", "ancam", "ancaman", "tekanan", "dihalangi", "halangi peliputan")):
        hits = [x for x in ("wartawan", "intimidasi", "ancam", "ancaman", "halangi peliputan") if has(text, x)]
        return "MEDIA_INFORMASI", "DUGAAN INTIMIDASI/HAMBATAN TERHADAP PERS", hits[:4]
    for issue_type, subtype, terms in ISSUE_PATTERNS:
        hits = [term for term in terms if has(text, term)]
        if hits:
            return issue_type, subtype, hits[:4]
    return "UMUM", "BELUM_TERIDENTIFIKASI", []


def analyze_article(title, summary="", police_context=True):
    title_text = norm(title)
    context = norm(f"{title} {summary}")
    issue_type, subtype, issue_hits = issue_analysis(context)
    handling_status, handling_hits, handling_points = handling_analysis(context)
    severity, severity_hits = _best_reason(context, SEVERITY_PATTERNS)
    authority, authority_hits = _best_reason(context, AUTHORITY_PATTERNS)
    impact, impact_hits = _best_reason(context, IMPACT_PATTERNS)
    if not police_context:
        authority = 0

    evidence = 2 if title_text else 0
    raw = severity + authority + impact + handling_points + evidence
    score = round(min(100, (raw / 72) * 100)) if raw else 0

    return {
        "issue_type": issue_type,
        "issue_subtype": subtype,
        "issue_evidence": issue_hits,
        "handling_status": handling_status,
        "handling_evidence": handling_hits,
        "attention_score": score,
        "attention_label": attention_label(score),
        "legacy_priority": legacy_priority(score),
        "attention_components": {
            "severity": severity,
            "authority": authority,
            "public_impact": impact,
            "handling": handling_points,
            "evidence": evidence,
        },
        "attention_evidence": {
            "severity": severity_hits,
            "authority": authority_hits,
            "public_impact": impact_hits,
            "handling": handling_hits,
        },
    }


def case_attention(articles, case=None, active_today=0):
    articles = list(articles or [])
    if not articles:
        return {"score": 0, "label": "Rendah", "priority": "low", "breakdown": {}, "evidence": {}}

    analyses = []
    sources = set()
    escalation = set()
    for article in articles:
        data = analyze_article(article.get("title", ""), article.get("summary", ""), True)
        analyses.append(data["attention_components"])
        src = norm(article.get("source") or article.get("publisher"))
        if src:
            sources.add(src)
        text = norm(article.get("title", ""))
        for _, terms in ESCALATION_PATTERNS:
            escalation.update(t for t in terms if has(text, t))

    severity = min(25, max(x.get("severity", 0) for x in analyses))
    authority = min(15, max(x.get("authority", 0) for x in analyses))
    impact = min(20, max(x.get("public_impact", 0) for x in analyses))
    handling = min(10, max(x.get("handling", 0) for x in analyses))
    evidence = min(5, max(x.get("evidence", 0) for x in analyses) + (2 if len(sources) >= 2 else 0))
    spread = 15 if len(sources) >= 8 else 12 if len(sources) >= 5 else 8 if len(sources) >= 3 else 4 if len(sources) >= 2 else 0
    esc = 5 if escalation else 0
    activity = min(5, active_today) if active_today else 0

    score = min(100, severity + authority + impact + handling + evidence + spread + esc + activity)
    return {
        "score": int(score),
        "label": attention_label(score),
        "priority": legacy_priority(score),
        "breakdown": {
            "severity": severity,
            "authority": authority,
            "public_impact": impact,
            "handling": handling,
            "evidence": evidence,
            "spread": spread,
            "escalation": esc,
            "current_activity": activity,
        },
        "evidence": {
            "unique_sources": len(sources),
            "active_today_articles": active_today,
            "escalation": sorted(escalation)[:5],
        },
    }
