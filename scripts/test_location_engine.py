from jagat_location_resolver_v2 import detect_location, base

CASES = {
    "Polres Batu Bara Tangkap Pelaku": (False, "LUAR JATIM", "", None, None),
    "Batu Bara: Polisi Sita Sabu": (False, "LUAR JATIM", "", None, None),
    "Polres Batu Ungkap Kasus Narkoba": (True, "Jawa Timur", "Batu", "POLRES BATU", None),
    "Polres Pelabuhan Tanjung Perak Amankan Pelaku": (True, "Jawa Timur", "Surabaya", "POLRES PELABUHAN TANJUNG PERAK", None),
    "Kapal Sandar di Tanjung Perak": (None, "BELUM TERPETAKAN", "", None, None),
    "Polsek Jogoroto Periksa Anggota": (True, "Jawa Timur", "Jombang", "POLRES JOMBANG", "POLSEK JOGOROTO"),
    "Berita Polda Jawa Timur Hari Ini": (True, "Jawa Timur", "Polda Jatim", None, None),
    "Satbrimob Polda Jatim Gelar Patroli": (True, "Jawa Timur", "Polda Jatim", None, None),
    "Bidpropam Polda Jatim Laksanakan Pengawasan": (True, "Jawa Timur", "Polda Jatim", None, None),
    "Ditreskrimsus Polda Jatim Ungkap Kasus": (True, "Jawa Timur", "Polda Jatim", None, None),
    "Ditres Siber Polda Jatim Tangani Laporan": (True, "Jawa Timur", "Polda Jatim", None, None),
    "Ditres PPA Polda Jatim Berikan Perlindungan": (True, "Jawa Timur", "Polda Jatim", None, None),
}

assert len(base.POLRES_MAP) == 39
for title, expected in CASES.items():
    got = detect_location(title)
    actual = (got["is_jatim"], got["region"], got["locality"], got["polres"], got["polsek"])
    assert actual == expected, f"{title!r}: {actual} != {expected}"

# Google News often carries the institution/location in the snippet rather
# than the headline. This must still resolve to Jatim/Lamongan/Tikung.
snippet_only = detect_location(
    "Pantau Panen dan Ketahanan Pangan",
    "Polsek Tikung memantau panen padi bersama petani di Lamongan.",
)
assert snippet_only["is_jatim"] is True, snippet_only
assert snippet_only["region"] == "Jawa Timur", snippet_only
assert snippet_only["locality"] == "Lamongan", snippet_only
assert snippet_only["polres"] == "POLRES LAMONGAN", snippet_only
assert snippet_only["polsek"] == "POLSEK TIKUNG", snippet_only

# A snippet can also carry an outside-Jatim location when the title is generic.
outside_snippet = detect_location(
    "Polres Tangkap Pelaku",
    "Peristiwa terjadi di Riau dan ditangani kepolisian setempat.",
)
assert outside_snippet["is_jatim"] is False, outside_snippet

print("LOCATION RESOLVER V2: OK")
print("Jatim area: 39 Polres + Polda Jatim")
print("Title + snippet + source resolution: OK")
