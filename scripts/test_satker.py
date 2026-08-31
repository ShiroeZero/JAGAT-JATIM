"""Tests for the first-class Polda Jatim satker model."""
import sys

from apply_satker import SATKER_POLDA_JATIM, detect_satker
from location_engine import POLRES_MAP


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected={expected!r}, actual={actual!r}")


def main():
    # Polda Jatim is an organisational satker, not a Polres/location entity.
    assert_equal(
        detect_satker({"title": "Kapolda Jawa Timur Berikan Arahan Kepada Anggota"}),
        SATKER_POLDA_JATIM,
        "Polda Jawa Timur detection",
    )
    assert_equal(
        detect_satker({"title": "Polda Jatim Tangani Kasus Viral"}),
        SATKER_POLDA_JATIM,
        "Polda Jatim detection",
    )
    assert_equal(
        detect_satker({"title": "Polres Jember Ungkap Kasus"}),
        None,
        "Polres must not be promoted to Polda satker",
    )

    if len(POLRES_MAP) != 39:
        raise AssertionError(f"Polres master must remain 39, found={len(POLRES_MAP)}")
    if SATKER_POLDA_JATIM in POLRES_MAP:
        raise AssertionError("Polda Jawa Timur must never be inserted into POLRES_MAP")

    print("SATKER TESTS: OK")
    print(f"Polres master: {len(POLRES_MAP)}")
    print(f"Satker master: {SATKER_POLDA_JATIM}")


if __name__ == "__main__":
    main()
