from analysis_engine import analyze_article, case_attention, ATTENTION_BANDS

cases = {
    "Anggota Resnarkoba Polres Bojonegoro Diduga Langgar SOP Penangkapan": "PROFESIONALISME_DAN_PROSEDUR",
    "Geliat Tambang Ilegal di Sukorejo Lamongan Belum Tersentuh Polisi": "AKTIVITAS_ILEGAL",
    "Datangi Polresta, PWI minta Kapolresta Tuban tindak tegas oknum Polri diduga intimidasi wartawan": "MEDIA_DAN_PERS",
}
for title, issue in cases.items():
    a = analyze_article(title, "", True)
    assert a["issue_type"] == issue, (title, a)
    assert 0 <= a["attention_score"] <= 100

sop = analyze_article(next(iter(cases)), "", True)
assert sop["attention_score"] >= 40, sop
assert sop["legacy_priority"] == "medium", sop
handling = analyze_article("Geliat Tambang Ilegal di Sukorejo Lamongan Belum Tersentuh Polisi", "", True)
assert handling["handling_status"] == "BELUM_DITANGANI", handling
assert case_attention([{"title": "Geliat Tambang Ilegal di Sukorejo Lamongan Belum Tersentuh Polisi"}], active_today=1)["score"] >= 40

enforcer = analyze_article("Polres Gresik Ungkap 14 Kasus Narkoba dalam Operasi Tumpas Semeru 2026, 17 Tersangka Diamankan", "", True)
assert enforcer["polri_relation"] == "PENEGAKAN_HUKUM", enforcer
assert enforcer["legacy_priority"] == "low", enforcer

sexual = analyze_article("Guru Ngaji di Banyuwangi Jadi Tersangka Dugaan Pencabulan Murid 8 Tahun, Polisi Langsung Menahan", "", True)
assert sexual["issue_type"] == "KEJAHATAN_SEKSUAL", sexual
assert sexual["attention_score"] >= 40, sexual

print("ANALYSIS ENGINE V6.5.2: OK")
