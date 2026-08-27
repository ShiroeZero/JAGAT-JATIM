from location_engine import detect_location, POLRES_MAP

CASES = {
    "Polres Batu Bara Tangkap Pelaku": (False, "LUAR JATIM", "", None, None),
    "Batu Bara: Polisi Sita Sabu": (False, "LUAR JATIM", "", None, None),
    "Polres Batu Ungkap Kasus Narkoba": (True, "Jawa Timur", "Batu", "POLRES BATU", None),
    "Polres Pelabuhan Tanjung Perak Amankan Pelaku": (True, "Jawa Timur", "Surabaya", "POLRES PELABUHAN TANJUNG PERAK", None),
    "Kapal Sandar di Tanjung Perak": (None, "BELUM TERPETAKAN", "", None, None),
    "Polsek Jogoroto Periksa Anggota": (True, "Jawa Timur", "Jombang", "POLRES JOMBANG", "POLSEK JOGOROTO"),
    "Berita Polda Jawa Timur Hari Ini": (True, "Jawa Timur", "", None, None),
}

assert len(POLRES_MAP) == 39
for title, expected in CASES.items():
    got = detect_location(title)
    actual = (got["is_jatim"], got["region"], got["locality"], got["polres"], got["polsek"])
    assert actual == expected, f"{title!r}: {actual} != {expected}"

print("LOCATION ENGINE V6.5: OK")
