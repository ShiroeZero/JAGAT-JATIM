"""Regression tests for JAGAT V6.5.6 final semantic correction."""
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
