# JAGAT — Jejaring Analisis & Garda Atensi Terpadu

JAGAT is an internal monitoring dashboard for news discovery, location normalization, canonical incident/case clustering, Jatim situational awareness, daily snapshots, historical archives, and operational reporting preparation.

## V6 architecture

```text
Discovery Matrix
    -> Google News collection
    -> Deduplication / relevance filtering
    -> Discovery-family classification
    -> Location + Polres normalization
    -> Canonical Incident / Case Engine
    -> Case Priority (severity + escalation + spread + activity)
    -> Today Snapshot + Archive
    -> Dashboard / Monitoring / Map / Archive
```

The frontend does not invent priority or case relationships. Article priority and Case priority are separate canonical fields produced by the backend.

## Discovery V6

V6 adds a discovery dictionary derived from the 2026 East Java headline corpora supplied for PNM development. The dictionary groups wording variants into families such as:

- Penanganan perkara / tangkap lepas
- Pungli / suap / gratifikasi / pemerasan / setoran
- Penyalahgunaan wewenang / ketidakprofesionalan / intervensi
- Etik / relasi pribadi / kekerasan seksual / aborsi / KDRT
- Backing / pembiaran aktivitas ilegal (tambang, judi, miras, rokok, BBM)
- Jurnalis / kebebasan informasi / intimidasi media
- Pelayanan SIM / Satpas / Samsat
- Keamanan / gangguan kamtibmas (demo ricuh, bentrok, serangan mako/pos)
- Dugaan pelanggaran oknum / Propam / etik-disiplin

Patterns are discovery signals, not factual determinations. Article wording still needs contextual evaluation.

`data/discovery_patterns_v6.json` is the canonical vocabulary used by the collector and Case Engine. The two supplied 2026 source corpora are preserved under `docs/`.

## Search coverage

The collector uses layered discovery rather than relying on a single national keyword query:

```text
General national queries
        +
Discovery-family queries
        +
Province discovery queries
        +
Jawa Timur Polres queries
        +
Active Case follow-up queries
```

This improves recall while keeping the existing deduplication and relevance filters. Google News remains a discovery source rather than a guarantee of exhaustive nationwide coverage.

## Main menu

- Dashboard — JAWA TIMUR + current day only.
- Monitoring — flexible explorer with Semua, Jawa Timur, Prioritas Tinggi, date range, region, Polres, scope, category, and search filters.
- Laporan — reserved for the report generator phase.
- Arsip — opens an independent snapshot for a selected date.

## Article and Case interaction

Every article card is clickable. The detail drawer shows source, time, region, Polres, category, scope, article priority, Case, and the original URL when available.

A Case represents one incident, not one article. Opening a Case resolves all linked article IDs against the relevant News dataset so the drawer can show every source belonging to that incident.

## Priority model

Article priority and Case priority are intentionally separate. Case priority is incident-level and considers severity, official escalation/handling, source spread, and current activity. A Medium article may therefore belong to a High-priority Case.

## Today and Archive

`data/today.json` is the current-day snapshot.

`data/archive/YYYY-MM-DD.json` is an independent snapshot for that date, including the articles and Case relationships available in that snapshot.

`data/archive/index.json` lists available snapshots.

## Matwil

The current Matwil mapping is stored at:

```text
data/matwil/current.json
```

The current source PDF is stored at:

```text
data/matwil/source.pdf
```

### Monthly manual update

1. Replace `data/matwil/source.pdf` with the newest signed PDF.
2. Install the local dependency once:

```bash
python -m pip install pypdf
```

3. Run:

```bash
python scripts/update_matwil.py
```

4. Inspect `data/matwil/current.json`.
5. Commit the updated JSON and source PDF.

## Validation

Run:

```bash
python scripts/validate_data.py
```

Validation checks include duplicate news IDs, duplicate Case IDs, Case/article references, duplicate Case membership, canonical Case priority, and current-day snapshot consistency.

## Workflow

GitHub Actions runs the collector hourly. YouTube collection is allowed to fail without blocking the news/case/snapshot pipeline. Pages deployment is integrated into the same workflow, so a successful collector run also publishes the current frontend/data bundle.

The sequence is:

```text
Collect News
Normalize Location
Build Cases
Check Case Database
Collect YouTube
Create Daily Snapshot
Build Archive Index
Validate Final Data
Check Frontend
Commit Data
Deploy GitHub Pages
```

The older standalone `pages-build-and-deployment` workflow is not required for normal operation.

## Access note

The dashboard is intentionally served without a frontend login gate. Access control, if required in the future, should be implemented at the hosting/authentication layer rather than by storing credentials in JavaScript.


## V6.1 corrections

- Geographic normalization uses the article title only; publisher/source names are never evidence for location.
- Canonical Jatim coverage is the 39 Polres Jatim plus explicit Jatim locality/province signals.
- Records without a canonical Jatim title signal are labeled `LUAR JATIM`.
- Discovery is Jatim-focused. The collector no longer fans out into one query family for every Indonesian province.
- National/general discovery remains as a supplement and can produce `LUAR JATIM` records.
- Daily dashboard metrics are Jatim-only.
- Monitoring uses the full news database plus explicit date filtering.
- Case priority remains separate from article priority.
- Archive uses its own snapshot for case/news detail.


## V6.4 — Stabilisasi data, lokasi, filter, dan UI

- 39 Polres Jawa Timur menjadi master data; dropdown filter hanya menampilkan Polres yang benar-benar muncul pada konteks data aktif.
- Lokasi artikel ditentukan dari judul artikel saja. Nama media/publisher tidak dipakai sebagai bukti geografis.
- Ambiguitas `Batu Bara` dilindungi agar tidak pernah dipetakan menjadi `Batu` Jawa Timur.
- Hirarki lokasi: Jawa Timur sebagai induk, lalu area/kabupaten/kota, lalu Polres jika institusinya disebut eksplisit.
- Dashboard fokus Jawa Timur hari ini. Klik wilayah membuka seluruh berita wilayah pada drawer, bukan berpindah ke Monitoring.
- Filter Monitoring menggunakan model facet/cascading: opsi setiap filter mengikuti tanggal dan filter aktif lainnya.
- Tab pintas `Semua / Jawa Timur / Prioritas Tinggi` dihapus dari Monitoring agar tidak terjadi dua sumber klasifikasi di UI.
- Case Engine memakai locality dan batas keras untuk Polres yang eksplisit berbeda.
- Validator memeriksa kesesuaian lokasi tersimpan dengan hasil engine dari judul.
- Semua kontrol UI dipaksa dark dan tipografi dinaikkan agar nyaman pada desktop maupun mobile.
