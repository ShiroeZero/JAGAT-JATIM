# Batch 02 — Deduplication & Case Clustering Audit Findings

- Audit run: [GitHub Actions run #1](https://github.com/ShiroeZero/JAGAT-JATIM/actions/runs/38586676637)
- Commit audited: `f7e67176ff9626328fcf267c59375d192803ab81`
- Result: SUCCESS
- Artifact: [jagat-batch02-dedup-audit](https://github.com/ShiroeZero/JAGAT-JATIM/actions/runs/38586676637/artifacts/11905447275)
- Mode: read-only. No article or case data was modified, deleted, re-keyed, or merged.

## Snapshot

| Signal | Audit result |
|---|---:|
| News articles | 5,000 |
| Case clusters | 1,407 |
| Canonical URL duplicate groups | 2 |
| Excess records in canonical URL duplicate groups | 2 |
| Normalized-title duplicate groups | 61 |
| Excess records in normalized-title groups | 64 |
| Candidate case pairs for review | 1 |
| News records without IDs | 0 |

The counts reflect this audit run and can change as the scheduled collector updates data.

## What the findings mean

### 1. Repeated URLs

Two canonical URL groups were found, each with two records. Examples include:
- `cianjurupdate.com/polisi-tangkap-satu-pelaku-penganiayaan-petugas-tnggp-di-gunung-putri-empat-masih-diburu`
- `lidik.id/sumsel/polisi-tangkap-2-terduga-pelaku-pembunuhan-dua-kakak-beradik-di-banyuasin`

These are high-confidence duplicate-article candidates. Before changing production records, compare record IDs, original URLs, source, dates, and article metadata. Preserve raw source provenance and avoid deleting an article merely to reduce the count.

### 2. Repeated normalized titles

There were 61 title groups with 64 excess records. The examples include repeated public-service / patrol announcements, as well as other repeated headlines. Identical titles can mean duplicated ingestion, syndication, or repeated routine activity; they are not by themselves proof of the same incident.

The audit also surfaced an exact-title group where the same source/title/date appears with distinct Google News RSS URLs. That is a strong candidate for ingestion duplication, but the stable publisher URL should be resolved before applying a deduplication rule.

### 3. Candidate case pair

The conservative case-pair scan found one pair:
- `CASE-001957`: “Polda Jatim Ungkap 1.870 Kasus Narkoba Triwulan III, Sita 86,5 Kg Sabu dan Ribuan Vape Etomidate”
- `CASE-001958`: “Ditresnarkoba Polda Jatim Sita 43 Kg Sabu dan Ribuan Vape Narkoba Etomidate”

This pair must remain **review-only**. One article may be a quarterly summary while the other describes a particular seizure; shared drug-related terms do not prove a single incident. Do not merge these cases without corroborating event identity and dates.

## Batch 02 implementation decisions

1. Keep all raw article records and original source URLs. No destructive deduplication.
2. Separate duplicate article detection from case clustering: same article is not the same thing as the same incident.
3. Add canonical URL comparison for tracking parameters, host casing, `www.`, and trailing slashes, but treat canonical URL equality as a review/dedup signal, not permission to delete.
4. Add stable tests for URL normalization, title normalization, distinct incidents with similar terms, same incident across different publishers, hard conflict between explicit different Polres, and duplicate article IDs inside a case.
5. Review and tighten the current `merge_duplicate_cases` rule with tests. Current code uses shared event/location terms and a title similarity threshold; the audit candidate shows why shared generic event terms must not be enough by themselves.
6. If a safe data-model change is implemented, prefer explicit duplicate metadata / canonical article identity while preserving original records and source provenance.
7. Run existing tests and new clustering tests before any production collector rebuild. Do not advance to Batch 03 until Batch 02's criteria pass.

## Scope boundary

This is a report of candidate findings, not a claim that production deduplication is fixed. The audit workflow did not invoke `scripts/process_cases.py`, the collector, or deployment. Implementation remains pending test-backed changes.
