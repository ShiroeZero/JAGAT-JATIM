"""JAGAT V6.5.6 final semantic corrections.

The V6.5.5 guardrail correctly catches the user's explicit integrity cases,
but its routine-enforcement fallback can override ordinary negative crime news
and turn it positive. This patch restores the intended distinction:
- crime news can remain negative even when police are the enforcer;
- only explicit institutional resolution/clarification gets the positive override;
- the two reported integrity cases remain negative.
"""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
ANALYSIS = BASE / "scripts" / "analysis_engine.py"
TESTS = BASE / "scripts" / "test_analysis_v656.py"
MARKER = "JAGAT_V656_FINAL_SEMANTIC_CORRECTION"


def patch_analysis():
    text = ANALYSIS.read_text(encoding="utf-8")
    if MARKER in text:
        return False

    # The V6.5.5 wrapper is already present. Add one final wrapper that fixes
    # the remaining semantic conflict without changing the underlying engine.
    wrapper = r'''

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

'''
    ANALYSIS.write_text(text.rstrip() + wrapper + "\n", encoding="utf-8")
    return True


def write_tests():
    content = '''"""Regression tests for JAGAT V6.5.6 final semantic correction."""
from analysis_engine import analyze_article


def check(title):
    return analyze_article(title, "", True)


# Serious crime handled by police stays negative; enforcement does not make the
# underlying crime itself positive.
sexual = check(
    "Kasus Ayah di Sumenep Diduga Cabuli Anak Kandung, Polisi: Terjadi Sejak 2021"
)
assert sexual["sentiment"] == "negative", sexual
assert sexual["issue_type"] == "KEJAHATAN_SEKSUAL", sexual
assert sexual["legacy_priority"] == "low", sexual

# User-reported false-neutral integrity case #1.
balong = check(
    "Kasus dugaan Tangkap Lepas Bayar Rp. 30 Juta di Polsek Balongpanggang, Polres Gresik Mencuat"
)
assert balong["sentiment"] == "negative", balong
assert balong["issue_type"] == "INTEGRITAS_DAN_KEUANGAN", balong
assert balong["attention_score"] >= 55, balong

# User-reported false-neutral integrity case #2.
sukorejo = check(
    "Warga Sukorejo Malang Dibawa Tiga Orang Mengaku Anggota Polda, Dugaan Setoran Rp15 Juta Mencuat"
)
assert sukorejo["sentiment"] == "negative", sukorejo
assert sukorejo["issue_type"] == "INTEGRITAS_DAN_KEUANGAN", sukorejo
assert sukorejo["polri_relation"] == "DUGAAN_MENGATASNAMAKAN_POLRI", sukorejo
assert sukorejo["attention_score"] >= 50, sukorejo

print("ANALYSIS ENGINE V6.5.6: OK")
'''
    TESTS.write_text(content, encoding="utf-8")
    return True


def main():
    changed = patch_analysis()
    changed = write_tests() or changed
    print(f"JAGAT V6.5.6 final semantic correction: {'CHANGED' if changed else 'OK'}")


if __name__ == "__main__":
    main()
