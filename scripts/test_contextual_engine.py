from contextual_engine import contextualize
from location_engine import detect_location

CASES = [
    ("Polsek Tikung Pantau Panen Padi, Dorong Warga Lamongan Perkuat Ketahanan Pangan", "Radar Bangsa", "neutral"),
    ("Polres Lamongan Tangkap Pelaku Narkoba", "", "positive"),
    ("Oknum Polisi Diduga Terima Uang Rp50 Juta untuk Lepas Tersangka", "", "negative"),
    ("Polisi Bantah Terlibat Pungli di Lamongan", "", "neutral"),
    ("Warga Keluhkan Pelayanan Polisi di Lamongan", "", "negative"),
    ("Polisi Jadi Korban Penembakan Saat Bertugas", "", "neutral"),
]

for title, summary, expected in CASES:
    out = contextualize(title, summary)
    got = out["sentiment"]
    assert got == expected, (title, expected, got, out)

loc = detect_location(
    "Police Goes To School Polres Lamongan Bentengi Pelajar",
    "Kegiatan berlangsung di Kecamatan Tikung, Kabupaten Lamongan.",
    source="contoh",
)
assert loc["is_jatim"] is True
assert loc["polres"] == "POLRES LAMONGAN"

print("Contextual engine tests: OK")
