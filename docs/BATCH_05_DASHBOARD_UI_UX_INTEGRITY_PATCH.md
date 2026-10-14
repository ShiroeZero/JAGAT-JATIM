# JAGAT-JATIM — Batch 05 Dashboard & UI/UX Integrity Patch

Status: PLANNED — scope locked; implementation must wait until Batch 02–04 are completed and validated.
Repository: ShiroeZero/JAGAT-JATIM
Purpose: fix dashboard count inconsistencies and make the dashboard, filters, regional views, and related pages reliable and coherent without removing existing functionality.

## Why this patch exists

The Batch 01 read-only baseline (2026-10-14) found 5,000 news records, 1,407 case clusters, and 1,700 article-to-case links. It also found 3,529 neutral, 1,069 positive, and 402 negative sentiment values, while the separate scope distribution was 3,529 neutral, 986 case, 402 negative, and 83 positive. These are different fields and must not be conflated. The dashboard must explain and consistently calculate each metric from a clearly defined population.

## Scope

### A. Metric integrity — highest priority
- Inventory every KPI card, chart, badge, regional count, case count, news count, filter count, and report summary.
- Define each metric explicitly: news articles, distinct cases, article-case links, sentiment, scope/category, mapped regions, unmapped records, and date window.
- Use a shared metric/selector layer for the same entity and active filters; avoid independent ad-hoc counting in separate UI components.
- Keep article counts separate from case counts and article-case link counts. Never label one as another.
- Deduplicate only according to an explicit identity rule. Repeated titles are review candidates, not automatic proof of duplicate incidents.
- Make chart totals and percentages reconcile with their declared denominator; document when categories are non-exclusive or a record can belong to multiple groups.
- Apply the same date, region, sentiment, scope, and text-search filters consistently to all widgets that claim to respond to those filters.
- Display an “as of” timestamp / data freshness indicator when available, and avoid implying real-time freshness when data is last pipeline-generated.
- Add a small metric definition/help affordance for potentially ambiguous numbers.

### B. Classification and color correctness
- Keep sentiment (positive / neutral / negative) distinct from scope or case/context classification.
- Audit sentiment badge colors, legend, regional drawer, filters, cards, and charts to ensure they read the sentiment field—not scope.
- Preserve manual-review overrides; clearly mark overridden vs automatically classified values.
- Do not present browser-local overrides as centrally saved. Explain their storage scope in the UI until central persistence is deliberately implemented.
- Make “unknown / needs review” visible rather than silently assigning a confident category.

### C. Dashboard information architecture
- Establish a clear hierarchy: headline KPIs → trend/overview → regional breakdown → priority/current cases → recent news → data-quality/freshness notes.
- Keep 39 Polres represented consistently and keep Polda Jatim as a separate SATKER; do not silently fold Polda into a Polres.
- Clearly distinguish “Belum Terpetakan” and “Luar Jatim” from valid East Java regional totals.
- Use consistent labels, number formatting, dates, severity/sentiment terminology, colors, legends, and tooltips across Dashboard, Monitoring, Laporan, Arsip, and regional/case detail views.
- Ensure case cards and news cards remain different entities and show the correct source/article relationship.

### D. Filtering, search, and interaction
- Provide clear active-filter chips and a one-action reset; show when zero results are caused by filters.
- Make search and filters compose predictably rather than one silently overriding another.
- Show result counts with a clear label (e.g. “12 berita dari 5000 total”), and specify whether the count is before or after filtering.
- Keep date filters available; ensure date boundaries/time zones behave consistently.
- Make interactive cards, dropdowns, tabs, drawers, sorting, and pagination keyboard-usable and visually indicate focus/selected states.
- Preserve the direct-to-dashboard/no-login behavior and existing navigation unless a separately approved change is documented.

### E. Visual and responsive UI/UX
- Audit desktop, tablet, and mobile widths; prevent overflow, clipped labels, overlapping cards, unreadable charts, and horizontal page scrolling.
- Standardize spacing, typography scale, card padding, border/radius, icon sizing, button states, and color tokens across styles.css, dashboard-modern.css, and page-specific styles.
- Keep sufficient contrast; do not rely on color alone to convey sentiment, priority, or status.
- Add consistent loading, empty, error, stale-data, and retry states. Do not show stale numbers as though the latest request succeeded.
- Make charts legible with labels/tooltips and usable on small screens; provide textual equivalents for key totals.
- Avoid unnecessary animation and expensive repeated rendering; preserve readable hierarchy and operational dashboard density.
- Ensure long titles, publisher names, dates, and regional names wrap or truncate safely without hiding critical information.

### F. Related pages and shared components
- Audit Dashboard, Monitoring, Laporan, Arsip, regional drawer, case detail, news detail, map/situational view, and shared navigation for mismatched labels, broken links, inconsistent filters, stale cache versions, and duplicate UI logic.
- Share common formatters, filter-state handling, empty/error states, badge semantics, and count definitions where safe.
- Keep source links and raw article/source provenance accessible.
- Confirm cache-busting versions are updated when frontend assets change and that GitHub Pages loads the intended versions.

## Acceptance criteria (must be evidenced)

1. A metric dictionary maps every visible KPI/chart to its source field, entity type, filters, and denominator.
2. With identical filters, every component reporting the same metric shows the same number.
3. News, distinct cases, and article-case links are separately labeled and reconcile to their own data sources.
4. Sentiment totals and scope totals are independently calculated; no component substitutes one field for the other.
5. Chart segments and displayed totals reconcile, or the UI explicitly explains a non-exclusive grouping.
6. The 39 Polres and Polda Jatim SATKER are represented according to the agreed model; unmapped/out-of-region records are not silently counted as mapped Polres.
7. Resetting filters returns all dependent components to the same baseline population.
8. Loading, empty, failure, and stale-data states are distinguishable.
9. Desktop and mobile smoke tests cover Dashboard, Monitoring, Laporan, Arsip, regional drawer, and case/news details.
10. Existing tests and validator remain enabled; new automated tests cover metric calculations, filter composition, sentiment/scope separation, and count reconciliation.
11. No news records, case records, raw source URLs, or existing features are deleted merely to make the numbers look consistent.
12. Commit, workflow run, test results, and deployment status are recorded before the batch is declared complete.

## Suggested implementation order inside Batch 05

1. Inventory current counters/charts and write the metric dictionary before changing presentation.
2. Reproduce each mismatch with fixed test data and identical filters.
3. Fix shared counting/filter logic first.
4. Fix sentiment/scope binding and badge/legend consistency.
5. Fix regional coverage, unmapped categories, and entity labels.
6. Polish layout, responsive behavior, accessibility, and loading/empty/error states.
7. Run automated tests plus desktop/mobile smoke checks; inspect production after deployment.

## Boundaries

- This is a planned patch specification, not a claim that the dashboard has already been fixed.
- Do not start Batch 05 until Batch 02 (deduplication/case clustering), Batch 03 (classification intelligence), and Batch 04 (pipeline efficiency) have passed their own gates.
- Do not alter collection cadence, validator rules, raw news history, or the 39-Polres/Polda separation as a side effect of UI work.
