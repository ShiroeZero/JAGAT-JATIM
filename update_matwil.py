import json
import os
import re
import sys
from datetime import datetime

try:
    from pypdf import PdfReader
except ImportError:
    raise SystemExit("Install pypdf first: python -m pip install pypdf")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCE = os.path.join(BASE, "data", "matwil", "source.pdf")
OUTPUT = os.path.join(BASE, "data", "matwil", "current.json")

POLRES_RE = re.compile(r"(POL(?:RES|RESTA|RESTABES)\s+[^;\n]+)", re.I)

def norm(text):
    return re.sub(r"\s+", " ", text or "").strip()

def clean_polres(value):
    value = norm(value).upper()
    value = value.replace(".", "")
    value = re.sub(r"\s+\d+$", "", value)
    value = re.sub(r"[;.:]+$", "", value).strip()
    return value

def find_unit_block(text, anchor, next_anchor=None):
    start = text.upper().find(anchor.upper())
    if start < 0:
        return ""
    end = text.upper().find(next_anchor.upper(), start + len(anchor)) if next_anchor else len(text)
    if end < 0:
        end = len(text)
    return text[start:end]

def extract_polres(block):
    found = []
    for match in POLRES_RE.finditer(block):
        value = clean_polres(match.group(1))
        value = re.sub(r"\s+\d+$", "", value)
        if value not in found:
            found.append(value)
    return found

def main():
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE

    if not os.path.exists(source):
        raise SystemExit(f"PDF tidak ditemukan: {source}")

    reader = PdfReader(source)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    # The current Sprin's territory table is grouped by functional
    # Paminal branches. These anchors correspond to the three Matwil
    # buckets used in the operational report:
    #   Unit 1 = Paurprodok + Kaurlitpers + Kanit I Paminal
    #   Unit 2 = Kaurbinpam + Kanit II Paminal
    #   Unit 3 = Panit III Paminal
    blocks = [
        (
            "MATWIL UNIT 1",
            [
                "PAURPRODOK",
                "KAURLITPERS",
                "KANIT I PAMINAL",
            ],
        ),
        (
            "MATWIL UNIT 2",
            [
                "KAURBINPAM",
                "KANIT II PAMINAL",
            ],
        ),
        (
            "MATWIL UNIT 3",
            [
                "PANIT III PAMINAL",
            ],
        ),
    ]

    all_anchors = [
        anchor
        for _, anchors in blocks
        for anchor in anchors
    ]

    def extract_group(anchor):
        start = text.upper().find(anchor.upper())
        if start < 0:
            return ""

        positions = []
        upper = text.upper()

        for other in all_anchors:
            if other.upper() == anchor.upper():
                continue
            pos = upper.find(other.upper(), start + len(anchor))
            if pos >= 0:
                positions.append(pos)

        end = min(positions) if positions else len(text)
        return text[start:end]

    units = []

    for label, anchors in blocks:
        collected = []

        for anchor in anchors:
            collected.extend(
                extract_polres(extract_group(anchor))
            )

        units.append({
            "unit": label,
            "anchors": anchors,
            "polres": sorted(dict.fromkeys(collected)),
        })

    month_match = re.search(
        r"(\d{1,2})\s*S\.?D\.?\s*(\d{1,2})\s+([A-Z]+)\s+(\d{4})",
        text.upper(),
    )

    period = ""
    effective_from = ""
    effective_to = ""

    if month_match:
        month_name = month_match.group(3)
        year = int(month_match.group(4))
        month_map = {
            "JANUARI":1,"FEBRUARI":2,"MARET":3,"APRIL":4,"MEI":5,"JUNI":6,
            "JULI":7,"AGUSTUS":8,"SEPTEMBER":9,"OKTOBER":10,"NOVEMBER":11,"DESEMBER":12
        }
        month = month_map.get(month_name)
        if month:
            period = f"{year:04d}-{month:02d}"
            effective_from = f"{year:04d}-{month:02d}-01"
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            from calendar import monthrange
            effective_to = f"{year:04d}-{month:02d}-{monthrange(year, month)[1]:02d}"

    output = {
        "period": period,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "source_file": os.path.basename(source),
        "generated_at": datetime.now().astimezone().isoformat(),
        "units": units,
        "notes": [
            "Mapping unit menggunakan kelompok Kanit I, Kanit II, dan Panit III pada Sprin.",
            "Periksa hasil parser sebelum commit jika format PDF bulan berikutnya berubah."
        ],
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("========================================")
    print("PNM MATWIL UPDATE")
    print("========================================")
    print(f"Source : {source}")
    print(f"Output : {OUTPUT}")
    for unit in units:
        print(f"{unit['unit']}: {len(unit['polres'])} wilayah")
    print("========================================")

if __name__ == "__main__":
    main()
