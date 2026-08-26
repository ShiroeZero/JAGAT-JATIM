# PNM — Polri Negative News Monitor

PNM is an internal monitoring dashboard for news, incident/case clustering, Jawa Timur mapping, daily snapshots, and historical archives.

## Core architecture

```text
News Collector
    -> Location normalization
    -> Canonical Incident / Case Engine
    -> Today Snapshot + Archive
    -> Dashboard / Monitoring / Map / Archive
```

The frontend does not invent priority or case relationships. Those values come from the canonical data produced by the backend.

## Main menu

- Dashboard — focused on the current day.
- Monitoring — one explorer with three modes: Semua, Jawa Timur, Prioritas Tinggi.
- Laporan — reserved for the report generator phase.
- Arsip — opens a complete snapshot for a selected date.

## Article interaction

Every article card is clickable. The detail drawer shows source, time, region, Polres, category, scope, priority, Case ID, and the original URL when available.

A Case is an incident, not a single article. A Case detail lists all source articles linked to that incident.

## Today and Archive

`data/today.json` is the current-day snapshot.

`data/archive/YYYY-MM-DD.json` is an independent snapshot of that date, including the articles and active cases for that day.

`data/archive/index.json` lists available snapshots.

## Matwil

The current Matwil mapping is stored at:

```text
data/matwil/current.json
```

The August 2026 source is the uploaded Sprin:

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

The parser groups the territories according to the operational Unit 1/2/3 anchors in the Sprin. If a future PDF changes its table structure, inspect the generated JSON before committing.

## Validation

Run:

```bash
python scripts/validate_data.py
```

This checks:

- duplicate news IDs
- duplicate Case IDs
- Case -> article references
- reverse article -> Case references
- duplicate article membership across Cases
- canonical Case priority
- today snapshot presence

## Workflow

GitHub Actions runs the collector hourly. YouTube collection is allowed to fail without blocking the news/case/snapshot pipeline, so a YouTube quota problem does not erase the daily news snapshot.

The workflow sequence is:

```text
Collect News
Normalize Location
Build Cases
Validate Data
Collect YouTube
Create Daily Snapshot
Build Archive Index
Validate Data
Commit Data
```

## Access note

The dashboard is intentionally served without a frontend login gate. Access control, if required in the future, should be implemented at the hosting/authentication layer rather than by storing credentials in JavaScript.
