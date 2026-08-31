"""JAGAT V6.5.7 semantic fallback for crime-news classification.

Some crime headlines involving police do not contain enough grammar for the
role detector, so the previous layers can leave them neutral. This final pass
uses a conservative rule: when a serious crime is explicitly present alongside
a Polri reference, classify the underlying crime as negative unless the text is
an explicit clarification/resolution context.
"""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
ANALYSIS = BASE / "scripts" / "analysis_engine.py"
TESTS = BASE / "scripts" / "test_analysis_v657.py"
MARKER = "JAGAT_V657_CRIME_SEMANTIC_FALLBACK"

WRAPPER = r'''

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
            r"\bpencabulan\b", r"\bpemerkosaan\b", r"\bperkosaan\b",
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

    has_police = _jagat_v657_has(text, police_ref)
    if not has_police:
        return result

    for issue_type, subtype, patterns in severe_crimes:
        if not _jagat_v657_has(text, patterns):
            continue

        # If the article explicitly says the police committed the crime, the
        # existing misconduct rules remain authoritative and can score higher.
        if result.get("polri_relation") == "SUBJEK_PERMASALAHAN":
            return result

        # Otherwise the article is about a serious crime that police are
        # handling/reporting. Keep it negative at a restrained score band.
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

'''


def main():
    text = ANALYSIS.read_text(encoding="utf-8")
    if MARKER not in text:
        ANALYSIS.write_text(text.rstrip() + WRAPPER + "\n", encoding="utf-8")

    TESTS.write_text(
        '''"""Regression tests for JAGAT V6.5.7 crime semantic fallback."""\n'
        'from analysis_engine import analyze_article\n\n'
        'sexual = analyze_article(\n'
        '    "Kasus Ayah di Sumenep Diduga Cabuli Anak Kandung, Polisi: Terjadi Sejak 2021",\n'
        '    "",\n'
        '    True,\n'
        ')\n'
        'assert sexual["sentiment"] == "negative", sexual\n'
        'assert sexual["issue_type"] == "KEJAHATAN_SEKSUAL", sexual\n'
        'assert sexual["legacy_priority"] == "low", sexual\n\n'
        'print("ANALYSIS ENGINE V6.5.7: OK")\n'''.replace("'\n", "\n"),
        encoding="utf-8",
    )
    print("JAGAT V6.5.7 semantic fallback: CHANGED")


if __name__ == "__main__":
    main()
