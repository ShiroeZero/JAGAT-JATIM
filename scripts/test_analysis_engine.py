from analysis_engine import analyze_article, ATTENTION_BANDS

cases = {
    "Anggota Resnarkoba Polres Bojonegoro Diduga Langgar SOP Penangkapan": "PELANGGARAN_PROSEDUR",
    "Geliat Tambang Ilegal di Sukorejo Lamongan Belum Tersentuh Polisi": "AKTIVITAS_ILEGAL",
    "PWI Tuban Kecam Dugaan Intimidasi Dua Wartawan oleh Perwira Polisi": "MEDIA_INFORMASI",
}
for title, issue in cases.items():
    a = analyze_article(title, "", True)
    assert a["issue_type"] == issue, (title, a)
    assert 0 <= a["attention_score"] <= 100

sop = analyze_article(cases.__iter__().__next__(), "", True)
assert sop["attention_score"] >= 25, sop
handling = analyze_article("Geliat Tambang Ilegal di Sukorejo Lamongan Belum Tersentuh Polisi", "", True)
assert handling["handling_status"] == "BELUM_DITANGANI", handling
print("ANALYSIS ENGINE V6.5.1: OK")

# AI-related fields are optional and do not affect deterministic analysis.
assert analyze_article("Anggota Polisi Diduga Langgar SOP", "", True)["issue_type"] == "PELANGGARAN_PROSEDUR"
