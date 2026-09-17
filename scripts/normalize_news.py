"""JAGAT contextual normalization pass.

Runs after collection so every article is re-evaluated from title + summary,
with location and contextual relation resolved before snapshots/case clustering.
"""
import json
import os
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

from jagat_location_resolver_v2 import detect_location
from fetch_news import discovery_matches
from contextual_engine import contextualize

NEWS_FILE = os.path.join(BASE, "data", "news.json")
ENGINE_VERSION = "contextual-v1.1"
LOCATION_ENGINE_VERSION = "location-v2-title-snippet-source"


def classify_existing(item):
    title = item.get("title", "")
    summary = item.get("summary", "") or item.get("description", "")
    source = item.get("source") or item.get("publisher") or ""
    text = f"{title} {summary}".strip()

    location = detect_location(title, summary, source=source)
    analysis = contextualize(title, summary)
    families, tags, hits = discovery_matches(text)

    # IMPORTANT: contextual scope is intentionally different from sentiment.
    # Enforcement can have positive sentiment while remaining in CASE scope.
    scope = analysis.get("scope") or (
        "negative" if analysis.get("sentiment") == "negative" else
        "positive" if analysis.get("sentiment") == "positive" else
        "neutral"
    )
    scope_label = analysis.get("scope_label") or analysis.get("sentiment_label") or "Netral"

    item.update({
        "is_jatim": location.get("is_jatim"),
        "region": location.get("region"),
        "locality": location.get("locality") or "",
        "area_label": location.get("area_label"),
        "polres": location.get("polres"),
        "polsek": location.get("polsek"),
        "location_confidence": location.get("confidence", 0),
        "location_evidence": location.get("evidence", []),
        "location_status": location.get("location_status"),
        "location_source": location.get("source") or LOCATION_ENGINE_VERSION,
        "category": analysis.get("classification_category") or "NETRAL / LAINNYA",
        "scope": scope,
        "scope_label": scope_label,
        "sentiment": analysis.get("sentiment", "neutral"),
        "sentiment_label": analysis.get("sentiment_label", "Netral"),
        "issue_type": analysis.get("issue_type"),
        "issue_subtype": analysis.get("issue_subtype"),
        "issue_evidence": analysis.get("issue_evidence", []),
        "polri_relation": analysis.get("polri_relation"),
        "polri_relation_evidence": analysis.get("polri_relation_evidence", []),
        "handling_status": analysis.get("handling_status"),
        "handling_evidence": analysis.get("handling_evidence", []),
        "assertion_status": analysis.get("assertion_status"),
        "assertion_confidence": analysis.get("assertion_confidence", 0),
        "assertion_evidence": analysis.get("assertion_evidence", []),
        "attention_score": analysis.get("contextual_attention_score", analysis.get("attention_score", 0)),
        "attention_label": analysis.get("attention_label"),
        "attention_components": analysis.get("attention_components", {}),
        "attention_evidence": analysis.get("attention_evidence", {}),
        "attention_reasons": analysis.get("contextual_reason", analysis.get("attention_reasons", [])),
        "contextual_flags": analysis.get("contextual_flags", {}),
        "priority": analysis.get("legacy_priority", "low"),
        "discovery_families": families,
        "discovery_tags": tags,
        "discovery_hits": hits,
        "classifier_version": ENGINE_VERSION,
        "analysis_engine_version": ENGINE_VERSION,
        "location_engine_version": LOCATION_ENGINE_VERSION,
        "classified_at": datetime.now(timezone.utc).isoformat(),
    })
    return item


def main():
    with open(NEWS_FILE, encoding="utf-8") as f:
        db = json.load(f)

    items = db.get("items", [])
    before_scope = {str(x.get("id") or x.get("url")): x.get("scope") for x in items}
    before_negative = sum(1 for x in items if x.get("scope") == "negative")

    for item in items:
        classify_existing(item)

    after_negative = sum(1 for x in items if x.get("scope") == "negative")
    after_positive = sum(1 for x in items if x.get("scope") == "positive")
    after_case = sum(1 for x in items if x.get("scope") == "case")
    after_neutral = sum(1 for x in items if x.get("scope") == "neutral")
    downgraded = 0
    promoted = 0
    preserved_case = 0
    for item in items:
        key = str(item.get("id") or item.get("url"))
        old = before_scope.get(key)
        new = item.get("scope")
        if old == "negative" and new == "neutral":
            downgraded += 1
        if old != "negative" and new == "negative":
            promoted += 1
        if new == "case":
            preserved_case += 1

    db["contextual_engine_version"] = ENGINE_VERSION
    db["location_engine_version"] = LOCATION_ENGINE_VERSION
    db["classifier_version"] = ENGINE_VERSION
    db["normalized_at"] = datetime.now(timezone.utc).isoformat()
    db["contextual_audit"] = {
        "records": len(items),
        "negative_before": before_negative,
        "negative_after": after_negative,
        "positive_after": after_positive,
        "case_after": after_case,
        "neutral_after": after_neutral,
        "downgraded_negative_to_neutral": downgraded,
        "promoted_to_negative": promoted,
        "case_scope_preserved": preserved_case,
    }

    tmp = NEWS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NEWS_FILE)

    print("========================================")
    print("JAGAT CONTEXTUAL NORMALIZATION V1.1")
    print("========================================")
    print(f"Records                     : {len(items)}")
    print(f"Negative before             : {before_negative}")
    print(f"Negative after              : {after_negative}")
    print(f"Positive after              : {after_positive}")
    print(f"Case after                  : {after_case}")
    print(f"Neutral after               : {after_neutral}")
    print(f"Negative -> Neutral         : {downgraded}")
    print(f"Promoted to Negative        : {promoted}")
    print(f"Case scope preserved        : {preserved_case}")
    print(f"Engine                      : {ENGINE_VERSION}")
    print(f"Location                    : {LOCATION_ENGINE_VERSION}")
    print("========================================")


if __name__ == "__main__":
    main()
