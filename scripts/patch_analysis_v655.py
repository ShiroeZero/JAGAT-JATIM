"""JAGAT V6.5.5 contextual classification guardrails.

This patch adds a final semantic pass after the existing analysis engine.
It fixes false-neutral/false-positive classifications without replacing the
existing engine or requiring external AI.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ANALYSIS = BASE / "scripts" / "analysis_engine.py"
NORMALIZER = BASE / "scripts" / "normalize_news.py"
TESTS = BASE / "scripts" / "test_analysis_v655.py"
MARKER = "JAGAT_V655_CONTEXT_GUARDRAIL_ACTIVE"

WRAPPER = r'''

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

'''


def patch_analysis():
    text = ANALYSIS.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    ANALYSIS.write_text(text.rstrip() + WRAPPER + "\n", encoding="utf-8")
    return True


def patch_normalizer():
    text = NORMALIZER.read_text(encoding="utf-8")
    marker = '"scope": "'  # only used for documentation sanity
    if '"scope_label": analysis["sentiment_label"]' in text and '"category": analysis.get("classification_category"' in text:
        return False
    old = '        "issue_type": analysis["issue_type"],\n'
    new = '''        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "issue_type": analysis["issue_type"],\n'''
    if old not in text:
        raise SystemExit("normalize_news patch target not found")
    NORMALIZER.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main():
    changed = patch_analysis()
    changed = patch_normalizer() or changed
    print(f"JAGAT V6.5.5 contextual guardrail: {'CHANGED' if changed else 'OK'}")


if __name__ == "__main__":
    main()
