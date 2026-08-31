"""Apply JAGAT V6.5.4 classification guardrails idempotently.

This patch is intentionally textual so GitHub Actions can update the live
repository without requiring a local clone in the development environment.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Patch target not found: {label}")
    if text.count(old) != 1:
        raise SystemExit(f"Patch target is not unique: {label} ({text.count(old)} matches)")
    return text.replace(old, new, 1)


def patch_analysis_engine() -> bool:
    path = BASE / "scripts" / "analysis_engine.py"
    text = path.read_text(encoding="utf-8")
    original = text

    text = text.replace(
        'JAGAT V6.5.3 deterministic context-aware article/case analysis.',
        'JAGAT V6.5.4 deterministic context-aware article/case analysis.',
        1,
    )

    text = replace_once(
        text,
        '    ("Pelayanan / prestasi", [\n        r"\\b(?:pelayanan|inovasi|prestasi|penghargaan|apresiasi)\\b.{0,100}\\b(?:polisi|polres|polda|polri)\\b",\n        r"\\b(?:polisi|polres|polda)\\b.{0,100}\\b(?:meraih|mendapat|menerima)\\b.{0,60}\\b(?:penghargaan|apresiasi|prestasi)\\b",\n    ]),\n]',
        '    ("Pelayanan / prestasi", [\n        r"\\b(?:pelayanan|inovasi|prestasi|penghargaan|apresiasi)\\b.{0,100}\\b(?:polisi|polres|polda|polri)\\b",\n        r"\\b(?:polisi|polres|polda)\\b.{0,100}\\b(?:meraih|mendapat|menerima)\\b.{0,60}\\b(?:penghargaan|apresiasi|prestasi)\\b",\n    ]),\n    ("Pemulihan / kompensasi", [\n        r"\\b(?:sudah|telah|resmi)\\s+(?:dibayar|membayar|diberi(?:kan)?|menerima)\\b.{0,100}\\b(?:ganti\\s+rugi|kompensasi|penggantian)\\b",\n        r"\\b(?:dibayar|membayar)\\b.{0,60}\\b(?:\\d+\\s*(?:x|kali)\\s*lipat|sepuluh\\s+kali)\\b",\n        r"\\b(?:ganti\\s+rugi|kompensasi|penggantian)\\b",\n    ]),\n]',
        'positive resolution patterns',
    )

    text = replace_once(
        text,
        'RISKY_MISCONDUCT_TERMS = {\n    "pungli", "suap", "pemerasan", "setoran", "upeti", "lepas tangkap",\n    "tangkap lepas", "tebusan", "penyalahgunaan wewenang", "langgar sop",\n    "melanggar sop", "intimidasi wartawan", "intimidasi jurnalis",\n    "penyiksaan", "penganiayaan", "penembakan", "mabuk", "perselingkuhan",\n    "asusila", "aborsi", "pencabulan",\n}\n\n\ndef norm(text):',
        'RISKY_MISCONDUCT_TERMS = {\n    "pungli", "suap", "pemerasan", "setoran", "upeti", "lepas tangkap",\n    "tangkap lepas", "tebusan", "penyalahgunaan wewenang", "langgar sop",\n    "melanggar sop", "intimidasi wartawan", "intimidasi jurnalis",\n    "penyiksaan", "penganiayaan", "penembakan", "mabuk", "perselingkuhan",\n    "asusila", "aborsi", "pencabulan",\n}\n\n# Benign procedural/evidentiary reporting should not be turned negative by\n# isolated words elsewhere in a headline or summary. Negative wording below\n# is deliberately required before this context can be treated as harmful.\nPROCEDURAL_NEUTRAL_PATTERNS = [\n    r"\\b(?:pengambilan|penyerahan|pengembalian|serah\\s+terima)\\s+barang\\s+bukti\\b",\n    r"\\b(?:mengambil|menyerahkan|mengembalikan)\\s+barang\\s+bukti\\b",\n]\n\nPROCEDURAL_NEGATIVE_PATTERNS = [\n    r"\\bbarang\\s+bukti\\b.{0,60}\\b(?:hilang|raib|dicuri|disalahgunakan)\\b",\n    r"\\b(?:pengambilan|penyerahan|penyitaan|pengembalian)\\b.{0,70}\\b(?:ilegal|tidak\\s+sah|melanggar\\s+sop|salah\\s+prosedur)\\b",\n]\n\n\ndef norm(text):',
        'procedural context constants',
    )

    text = replace_once(
        text,
        'def has(text, phrase):\n    return re.search(\n        r"(?<![a-z0-9])" + re.escape(norm(phrase)) + r"(?![a-z0-9])",\n        norm(text),\n    ) is not None\n\n\ndef any_phrase(text, phrases):',
        'def has(text, phrase):\n    return re.search(\n        r"(?<![a-z0-9])" + re.escape(norm(phrase)) + r"(?![a-z0-9])",\n        norm(text),\n    ) is not None\n\n\ndef has_nonnegated(text, phrase):\n    """Match a phrase unless it is directly negated in local context."""\n    t = norm(text)\n    p = norm(phrase)\n    pattern = r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])"\n    for match in re.finditer(pattern, t):\n        prefix = t[max(0, match.start() - 42):match.start()]\n        if re.search(r"\\b(?:tidak|tak|bukan|tanpa)\\b(?:\\s+\\w+){0,3}\\s*$", prefix):\n            continue\n        return True\n    return False\n\n\ndef any_phrase(text, phrases):',
        'negation-aware phrase helper',
    )

    text = replace_once(
        text,
        '    for issue_type, subtype, pattern in combo_patterns:\n        if re.search(pattern, text):\n            return issue_type, subtype, [pattern]\n\n    best = None\n    for issue_type, subtype, terms in ISSUE_PATTERNS:\n        hits = [term for term in terms if has(text, term)]',
        '    for issue_type, subtype, pattern in combo_patterns:\n        for match in re.finditer(pattern, text):\n            prefix = text[max(0, match.start() - 42):match.start()]\n            if re.search(r"\\b(?:tidak|tak|bukan|tanpa)\\b(?:\\s+\\w+){0,3}\\s*$", prefix):\n                continue\n            return issue_type, subtype, [pattern]\n\n    best = None\n    for issue_type, subtype, terms in ISSUE_PATTERNS:\n        hits = [term for term in terms if has_nonnegated(text, term)]',
        'negation-aware issue selection',
    )

    text = replace_once(
        text,
        'def detect_positive(text):\n    for label, patterns in POSITIVE_PATTERNS:\n        hits = [pattern for pattern in patterns if re.search(pattern, text)]\n        if hits:\n            return label, hits[:3]\n    return None, []\n\n\ndef detect_role(text):',
        'def detect_positive(text):\n    for label, patterns in POSITIVE_PATTERNS:\n        hits = [pattern for pattern in patterns if re.search(pattern, text)]\n        if hits:\n            return label, hits[:3]\n    return None, []\n\n\ndef detect_procedural_context(text):\n    negative = any(re.search(pattern, text) for pattern in PROCEDURAL_NEGATIVE_PATTERNS)\n    if negative:\n        return None, []\n    hits = [pattern for pattern in PROCEDURAL_NEUTRAL_PATTERNS if re.search(pattern, text)]\n    if hits:\n        return "Prosedur barang bukti", hits[:3]\n    return None, []\n\n\ndef detect_role(text):',
        'procedural context detector',
    )

    text = replace_once(
        text,
        '    for pattern in ENFORCER_PATTERNS:\n        if re.search(pattern, text):\n            return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak"\n\n    if re.search',
        '    for pattern in ENFORCER_PATTERNS:\n        if re.search(pattern, text):\n            return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak"\n\n    procedural_label, _procedural_hits = detect_procedural_context(text)\n    if procedural_label and any_phrase(text, ["polisi", "polres", "polresta", "polrestabes", "polda"]):\n        return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak dalam prosedur barang bukti"\n\n    if re.search',
        'procedural enforcement role',
    )

    text = replace_once(
        text,
        '    positive_label, positive_hits = detect_positive(context)\n    issue_type, issue_subtype, issue_hits = first_issue(context)',
        '    positive_label, positive_hits = detect_positive(context)\n    procedural_label, procedural_hits = detect_procedural_context(context)\n    issue_type, issue_subtype, issue_hits = first_issue(context)',
        'analyze article procedural evidence',
    )

    text = replace_once(
        text,
        '    elif positive_label:\n        sentiment = "positive"\n        sentiment_label = "Positif"\n    elif issue_type != "UMUM" or handling_status == "BELUM_DITANGANI":',
        '    elif positive_label or procedural_label:\n        sentiment = "positive"\n        sentiment_label = "Positif"\n    elif issue_type != "UMUM" or handling_status == "BELUM_DITANGANI":',
        'positive/procedural sentiment precedence',
    )

    text = replace_once(
        text,
        '        "positive": positive_hits,\n    },\n    "attention_reasons": reasons[:8],',
        '        "positive": positive_hits,\n        "procedural": procedural_hits,\n    },\n    "attention_reasons": reasons[:8],',
        'procedural evidence output',
    )

    text = text.replace('classifier_version": "news-v6.5.3"', 'classifier_version": "news-v6.5.4"')
    text = text.replace('analysis_engine_version": "analysis-v6.5.3"', 'analysis_engine_version": "analysis-v6.5.4"')

    path.write_text(text, encoding="utf-8")
    return text != original


def patch_versions() -> bool:
    changed = False
    for filename in ("normalize_news.py", "process_cases.py"):
        path = BASE / "scripts" / filename
        text = path.read_text(encoding="utf-8")
        original = text
        text = text.replace("v6.5.3", "v6.5.4")
        if filename == "normalize_news.py":
            text = text.replace("analysis-v6.5.3", "analysis-v6.5.4")
        path.write_text(text, encoding="utf-8")
        changed = changed or text != original
    return changed


def patch_test_suite() -> bool:
    path = BASE / "scripts" / "test_analysis_engine.py"
    text = path.read_text(encoding="utf-8")
    original = text
    marker = 'print("ANALYSIS ENGINE V6.5.3: OK")'
    additions = r'''

# 8) Procedural barang-bukti reporting is not negative by itself.
evidence_pickup = analyze_article(
    "Polrestabes Surabaya Lakukan Pengambilan Barang Bukti untuk Proses Pemeriksaan",
    "Barang bukti diambil sebagai bagian dari proses resmi.",
    True,
)
assert evidence_pickup["sentiment"] in {"positive", "neutral"}, evidence_pickup
assert evidence_pickup["issue_type"] == "UMUM", evidence_pickup

# 9) Explicit compensation/resolution is positive, not a misconduct label.
compensation = analyze_article(
    "Kapolrestabes Surabaya Bayar 10 Kali Lipat kepada Pihak Terkait sebagai Penggantian",
    "Pembayaran dilakukan sebagai bentuk penyelesaian.",
    True,
)
assert compensation["sentiment"] == "positive", compensation
assert compensation["issue_type"] == "UMUM", compensation

# 10) Negated integrity language must not create a false misconduct issue.
rebuttal = analyze_article(
    "Kapolrestabes Surabaya Tegaskan Tidak Ada Pungli, Pihak Terkait Sudah Dibayar 10 Kali Lipat",
    "Klarifikasi menyebut pembayaran telah diselesaikan.",
    True,
)
assert rebuttal["sentiment"] == "positive", rebuttal
assert rebuttal["issue_type"] == "UMUM", rebuttal

'''
    if marker not in text:
        raise SystemExit("Patch target not found: analysis test marker")
    text = text.replace(marker, additions + 'print("ANALYSIS ENGINE V6.5.4: OK")', 1)
    path.write_text(text, encoding="utf-8")
    return text != original


def patch_frontend() -> bool:
    path = BASE / "index.html"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace('  <link rel="stylesheet" href="dashboard-modern.css?v=6.7.0">\n', '')
    text = text.replace('  <script defer src="dashboard-modern.js?v=6.7.0"></script>\n', '')
    text = text.replace('<link rel="stylesheet" href="dashboard-modern.css?v=6.7.0">\n', '')
    text = text.replace('<script defer src="dashboard-modern.js?v=6.7.0"></script>\n', '')
    path.write_text(text, encoding="utf-8")
    return text != original


def main() -> None:
    changed = patch_analysis_engine()
    changed = patch_versions() or changed
    changed = patch_test_suite() or changed
    changed = patch_frontend() or changed
    print(f"V6.5.4 classification/dashboard patch: {'CHANGED' if changed else 'OK'}")


if __name__ == "__main__":
    main()
