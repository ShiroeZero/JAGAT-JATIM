"""Regression tests for JAGAT V6.5.5 contextual classification."""
from analysis_engine import analyze_article


def check(title, expected_sentiment, expected_issue=None):
    result = analyze_article(title, "", True)
    assert result["sentiment"] == expected_sentiment, result
    if expected_issue:
        assert result["issue_type"] == expected_issue, result
    return result


# Exact false-negative reported by the operator: tangkap lepas + payment.
r1 = check(
    "Kasus dugaan Tangkap Lepas Bayar Rp. 30 Juta di Polsek Balongpanggang, Polres Gresik Mencuat",
    "negative",
    "INTEGRITAS_DAN_KEUANGAN",
)
assert r1["attention_score"] >= 55, r1

# Exact false-negative reported by the operator: claimed Polda identity + setoran.
r2 = check(
    "Warga Sukorejo Malang Dibawa Tiga Orang Mengaku Anggota Polda, Dugaan Setoran Rp15 Juta Mencuat",
    "negative",
    "INTEGRITAS_DAN_KEUANGAN",
)
assert r2["polri_relation"] == "DUGAAN_MENGATASNAMAKAN_POLRI", r2
assert r2["attention_score"] >= 50, r2

# Resolution/rebuttal should remain positive rather than inherit a financial issue.
r3 = check(
    "Kapolrestabes Surabaya Bayar 10 Kali Lipat kepada Pihak Terkait sebagai Penggantian",
    "positive",
    "UMUM",
)
assert r3["attention_score"] <= 35, r3

r4 = check(
    "Kapolrestabes Surabaya Tegaskan Tidak Ada Pungli, Pihak Terkait Sudah Dibayar 10 Kali Lipat",
    "positive",
    "UMUM",
)
assert r4["attention_score"] <= 35, r4

# Ordinary police action remains positive.
r5 = check(
    "Polres Gresik Ungkap 14 Kasus Narkoba, 17 Tersangka Diamankan",
    "positive",
)
assert r5["polri_relation"] == "PENEGAKAN_HUKUM", r5

print("ANALYSIS ENGINE V6.5.5: OK")
