from analysis_engine import analyze_article, case_attention


# 1) Serious crime handled by police is NOT automatically high.
sexual = analyze_article(
    "Guru Ngaji di Banyuwangi Jadi Tersangka Dugaan Pencabulan Murid 8 Tahun, Polisi Langsung Menahan",
    "",
    True,
)
assert sexual["issue_type"] == "KEJAHATAN_SEKSUAL", sexual
assert sexual["polri_relation"] == "PENEGAKAN_HUKUM", sexual
assert sexual["sentiment"] == "negative", sexual
assert sexual["attention_score"] <= 39, sexual

# 2) Police/personnel as subject + SOP violation = at least medium.
sop = analyze_article(
    "Anggota Resnarkoba Polres Bojonegoro Diduga Langgar SOP Penangkapan",
    "",
    True,
)
assert sop["issue_type"] == "PROFESIONALISME_DAN_PROSEDUR", sop
assert sop["polri_relation"] == "SUBJEK_PERMASALAHAN", sop
assert sop["attention_score"] >= 40, sop
assert sop["legacy_priority"] == "medium", sop

# 3) Police as subject + extortion/bribe + nominal = high.
bribe = analyze_article(
    "Oknum Polisi Diduga Minta Rp50 Juta untuk Lepas Tersangka",
    "",
    True,
)
assert bribe["issue_type"] == "INTEGRITAS_DAN_KEUANGAN", bribe
assert bribe["polri_relation"] == "SUBJEK_PERMASALAHAN", bribe
assert bribe["attention_score"] >= 70, bribe
assert bribe["sentiment"] == "negative", bribe

# 4) Routine enforcement is positive and capped.
enforcer = analyze_article(
    "Polres Gresik Ungkap 14 Kasus Narkoba dalam Operasi Tumpas Semeru 2026, 17 Tersangka Diamankan",
    "",
    True,
)
assert enforcer["polri_relation"] == "PENEGAKAN_HUKUM", enforcer
assert enforcer["sentiment"] == "positive", enforcer
assert enforcer["attention_score"] <= 39, enforcer

# 5) Illegal activity with no police response is negative and at least medium.
handling = analyze_article(
    "Geliat Tambang Ilegal di Sukorejo Lamongan Belum Tersentuh Polisi",
    "",
    True,
)
assert handling["issue_type"] == "AKTIVITAS_ILEGAL", handling
assert handling["handling_status"] == "BELUM_DITANGANI", handling
assert handling["sentiment"] == "negative", handling
assert handling["attention_score"] >= 40, handling

# 6) Direct serious police misconduct should be high.
serious = analyze_article(
    "Oknum Polisi Diduga Menembak Warga hingga Tewas di Jawa Timur",
    "",
    True,
)
assert serious["polri_relation"] == "SUBJEK_PERMASALAHAN", serious
assert serious["issue_type"] == "KEKERASAN_DAN_KEKUATAN", serious
assert serious["attention_score"] >= 70, serious

# 7) Case score follows the same semantics.
case = case_attention([
    {
        "title": "Oknum Polisi Diduga Minta Rp50 Juta untuk Lepas Tersangka",
        "source": "Media A",
    },
    {
        "title": "Oknum Polisi Diduga Minta Rp50 Juta untuk Lepas Tersangka",
        "source": "Media B",
    },
], active_today=2)
assert case["priority"] == "high", case
assert case["label"] == "Tinggi", case

print("ANALYSIS ENGINE V6.5.3: OK")
