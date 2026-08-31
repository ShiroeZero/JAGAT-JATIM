"""Regression tests for JAGAT V6.5.7 crime semantic fallback."""
from analysis_engine import analyze_article

sexual = analyze_article(
    "Kasus Ayah di Sumenep Diduga Cabuli Anak Kandung, Polisi: Terjadi Sejak 2021",
    "",
    True,
)
assert sexual["sentiment"] == "negative", sexual
assert sexual["issue_type"] == "KEJAHATAN_SEKSUAL", sexual
assert sexual["legacy_priority"] == "low", sexual

balong = analyze_article(
    "Kasus dugaan Tangkap Lepas Bayar Rp. 30 Juta di Polsek Balongpanggang, Polres Gresik Mencuat",
    "",
    True,
)
assert balong["sentiment"] == "negative", balong
assert balong["issue_type"] == "INTEGRITAS_DAN_KEUANGAN", balong
assert balong["attention_score"] >= 55, balong

sukorejo = analyze_article(
    "Warga Sukorejo Malang Dibawa Tiga Orang Mengaku Anggota Polda, Dugaan Setoran Rp15 Juta Mencuat",
    "",
    True,
)
assert sukorejo["sentiment"] == "negative", sukorejo
assert sukorejo["issue_type"] == "INTEGRITAS_DAN_KEUANGAN", sukorejo
assert sukorejo["polri_relation"] == "DUGAAN_MENGATASNAMAKAN_POLRI", sukorejo
assert sukorejo["attention_score"] >= 50, sukorejo

print("ANALYSIS ENGINE V6.5.7: OK")
