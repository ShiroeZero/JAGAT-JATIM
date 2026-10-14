"""Batch 02 regression tests for conservative case deduplication."""
from process_cases import case_merge_candidate, merge_duplicate_cases


def case(case_id, title, *, polres="POLRES GRESIK", locality="Gresik",
         events=None, locations=None, first="2026-09-01T00:00:00+00:00",
         last="2026-09-02T00:00:00+00:00", article_ids=None):
    article_ids = list(article_ids or [])
    return {
        "case_id": case_id,
        "title": title,
        "polres": polres,
        "locality": locality,
        "event_terms": list(events or ["penganiayaan", "tangkap"]),
        "location_terms": list(locations or ["gresik"]),
        "first_seen": first,
        "last_seen": last,
        "article_ids": article_ids,
        "articles": [{"id": aid, "title": aid} for aid in article_ids],
        "article_count": len(article_ids),
        "incident_terms": [],
        "is_jatim": True,
    }


# Same incident: strong headline, event, geography and time agreement.
same_a = case(
    "CASE-1",
    "Polres Gresik Tangkap Pelaku Penganiayaan di Balongpanggang",
    article_ids=["news-a"],
)
same_b = case(
    "CASE-2",
    "Polres Gresik Tangkap Pelaku Penganiayaan Balongpanggang",
    article_ids=["news-b"],
)
assert case_merge_candidate(same_a, same_b)

# Similar crime vocabulary alone must not merge unrelated incidents.
different_incident = case(
    "CASE-3",
    "Polres Gresik Tangkap Pelaku Penganiayaan di Manyar",
    events=["penganiayaan", "tangkap"],
    locations=["manyar"],
)
different_incident["title"] = "Polres Gresik Tangkap Pelaku Penganiayaan Kasus Lain di Manyar"
assert not case_merge_candidate(same_a, different_incident)

# Explicit Polres and locality conflicts are hard boundaries.
other_polres = case("CASE-4", same_b["title"], polres="POLRES SIDOARJO", locality="Sidoarjo")
assert not case_merge_candidate(same_a, other_polres)
other_locality = case("CASE-5", same_b["title"], locality="Lamongan")
assert not case_merge_candidate(same_a, other_locality)

# Cases outside the configured time window must not be consolidated.
old_case = case(
    "CASE-6",
    same_b["title"],
    first="2025-01-01T00:00:00+00:00",
    last="2025-01-02T00:00:00+00:00",
)
assert not case_merge_candidate(same_a, old_case)

# Missing dates are not enough evidence for an automatic merge.
missing_dates = case("CASE-7", same_b["title"], first="", last="")
assert not case_merge_candidate(same_a, missing_dates)

# Actual consolidation keeps unique article IDs and recomputes the count.
merge_a = case("CASE-8", same_a["title"], article_ids=["news-a"])
merge_b = case("CASE-9", same_b["title"], article_ids=["news-b", "news-a"])
merged = [merge_a, merge_b]
count = merge_duplicate_cases(merged)
assert count == 1, count
assert len(merged) == 1, len(merged)
assert set(merged[0]["article_ids"]) == {"news-a", "news-b"}, merged[0]["article_ids"]
assert merged[0]["article_count"] == 2, merged[0]["article_count"]

print("BATCH 02 DEDUP REGRESSION TESTS: OK")
