"""Robust, idempotent JAGAT V6.5.4 classification remediation.

The previous textual patch was too strict and could fail after a partial edit.
This version checks each transformation independently and never aborts merely
because one optional target has already been changed.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def replace_if_present(text: str, old: str, new: str) -> tuple[str, bool]:
    if old in text:
        return text.replace(old, new, 1), True
    return text, False


def patch_analysis() -> bool:
    path = BASE / "scripts" / "analysis_engine.py"
    text = path.read_text(encoding="utf-8")
    original = text

    text, _ = replace_if_present(
        text,
        "JAGAT V6.5.3 deterministic context-aware article/case analysis.",
        "JAGAT V6.5.4 deterministic context-aware article/case analysis.",
    )

    old = '''    ("Pelayanan / prestasi", [
        r"\\b(?:pelayanan|inovasi|prestasi|penghargaan|apresiasi)\\b.{0,100}\\b(?:polisi|polres|polda|polri)\\b",
        r"\\b(?:polisi|polres|polda)\\b.{0,100}\\b(?:meraih|mendapat|menerima)\\b.{0,60}\\b(?:penghargaan|apresiasi|prestasi)\\b",
    ]),
]'''
    new = '''    ("Pelayanan / prestasi", [
        r"\\b(?:pelayanan|inovasi|prestasi|penghargaan|apresiasi)\\b.{0,100}\\b(?:polisi|polres|polda|polri)\\b",
        r"\\b(?:polisi|polres|polda)\\b.{0,100}\\b(?:meraih|mendapat|menerima)\\b.{0,60}\\b(?:penghargaan|apresiasi|prestasi)\\b",
    ]),
    ("Pemulihan / kompensasi", [
        r"\\b(?:sudah|telah|resmi)\\s+(?:dibayar|membayar|diberi(?:kan)?|menerima)\\b.{0,100}\\b(?:ganti\\s+rugi|kompensasi|penggantian)\\b",
        r"\\b(?:dibayar|membayar)\\b.{0,60}\\b(?:\\d+\\s*(?:x|kali)\\s*lipat|sepuluh\\s+kali)\\b",
        r"\\b(?:ganti\\s+rugi|kompensasi|penggantian)\\b",
    ]),
]'''
    text, _ = replace_if_present(text, old, new)

    old = '''RISKY_MISCONDUCT_TERMS = {
    "pungli", "suap", "pemerasan", "setoran", "upeti", "lepas tangkap",
    "tangkap lepas", "tebusan", "penyalahgunaan wewenang", "langgar sop",
    "melanggar sop", "intimidasi wartawan", "intimidasi jurnalis",
    "penyiksaan", "penganiayaan", "penembakan", "mabuk", "perselingkuhan",
    "asusila", "aborsi", "pencabulan",
}


def norm(text):'''
    new = '''RISKY_MISCONDUCT_TERMS = {
    "pungli", "suap", "pemerasan", "setoran", "upeti", "lepas tangkap",
    "tangkap lepas", "tebusan", "penyalahgunaan wewenang", "langgar sop",
    "melanggar sop", "intimidasi wartawan", "intimidasi jurnalis",
    "penyiksaan", "penganiayaan", "penembakan", "mabuk", "perselingkuhan",
    "asusila", "aborsi", "pencabulan",
}

PROCEDURAL_NEUTRAL_PATTERNS = [
    r"\\b(?:pengambilan|penyerahan|pengembalian|serah\\s+terima)\\s+barang\\s+bukti\\b",
    r"\\b(?:mengambil|menyerahkan|mengembalikan)\\s+barang\\s+bukti\\b",
]

PROCEDURAL_NEGATIVE_PATTERNS = [
    r"\\bbarang\\s+bukti\\b.{0,60}\\b(?:hilang|raib|dicuri|disalahgunakan)\\b",
    r"\\b(?:pengambilan|penyerahan|penyitaan|pengembalian)\\b.{0,70}\\b(?:ilegal|tidak\\s+sah|melanggar\\s+sop|salah\\s+prosedur)\\b",
]


def norm(text):'''
    text, _ = replace_if_present(text, old, new)

    old = '''def has(text, phrase):
    return re.search(
        r"(?<![a-z0-9])" + re.escape(norm(phrase)) + r"(?![a-z0-9])",
        norm(text),
    ) is not None


def any_phrase(text, phrases):'''
    new = '''def has(text, phrase):
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
        if re.search(r"\\b(?:tidak|tak|bukan|tanpa)\\b(?:\\s+\\w+){0,3}\\s*$", prefix):
            continue
        return True
    return False


def any_phrase(text, phrases):'''
    text, _ = replace_if_present(text, old, new)

    old = '        hits = [term for term in terms if has(text, term)]'
    new = '        hits = [term for term in terms if has_nonnegated(text, term)]'
    text, _ = replace_if_present(text, old, new)

    old = '''def detect_positive(text):
    for label, patterns in POSITIVE_PATTERNS:
        hits = [pattern for pattern in patterns if re.search(pattern, text)]
        if hits:
            return label, hits[:3]
    return None, []


def detect_role(text):'''
    new = '''def detect_positive(text):
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


def detect_role(text):'''
    text, _ = replace_if_present(text, old, new)

    old = '''    for pattern in ENFORCER_PATTERNS:
        if re.search(pattern, text):
            return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak"

    if re.search'''
    new = '''    for pattern in ENFORCER_PATTERNS:
        if re.search(pattern, text):
            return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak"

    procedural_label, _procedural_hits = detect_procedural_context(text)
    if procedural_label and any_phrase(text, ["polisi", "polres", "polresta", "polrestabes", "polda"]):
        return "PENEGAKAN_HUKUM", "Polri sebagai pihak penindak dalam prosedur barang bukti"

    if re.search'''
    text, _ = replace_if_present(text, old, new)

    old = '''    positive_label, positive_hits = detect_positive(context)
    issue_type, issue_subtype, issue_hits = first_issue(context)'''
    new = '''    positive_label, positive_hits = detect_positive(context)
    procedural_label, procedural_hits = detect_procedural_context(context)
    issue_type, issue_subtype, issue_hits = first_issue(context)'''
    text, _ = replace_if_present(text, old, new)

    old = '''    elif positive_label:
        sentiment = "positive"
        sentiment_label = "Positif"
    elif issue_type != "UMUM" or handling_status == "BELUM_DITANGANI":'''
    new = '''    elif positive_label or procedural_label:
        sentiment = "positive"
        sentiment_label = "Positif"
    elif issue_type != "UMUM" or handling_status == "BELUM_DITANGANI":'''
    text, _ = replace_if_present(text, old, new)

    path.write_text(text, encoding="utf-8")
    return text != original


def patch_versions() -> bool:
    changed = False
    for filename in ("normalize_news.py", "process_cases.py"):
        path = BASE / "scripts" / filename
        text = path.read_text(encoding="utf-8")
        original = text
        text = text.replace("v6.5.3", "v6.5.4")
        path.write_text(text, encoding="utf-8")
        changed = changed or text != original
    return changed


def patch_tests() -> bool:
    path = BASE / "scripts" / "test_analysis_engine.py"
    text = path.read_text(encoding="utf-8")
    original = text
    if "Procedural barang-bukti reporting" in text:
        return False
    marker = 'print("ANALYSIS ENGINE V6.5.3: OK")'
    if marker not in text:
        marker = 'print("ANALYSIS ENGINE V6.5.4: OK")'
        if marker in text:
            return False
        raise SystemExit("analysis test marker not found")
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
    text = text.replace(marker, additions + 'print("ANALYSIS ENGINE V6.5.4: OK")', 1)
    path.write_text(text, encoding="utf-8")
    return text != original


def main() -> None:
    changed = patch_analysis()
    changed = patch_versions() or changed
    changed = patch_tests() or changed
    print(f"JAGAT V6.5.4 remediation: {'CHANGED' if changed else 'OK'}")


if __name__ == "__main__":
    main()
