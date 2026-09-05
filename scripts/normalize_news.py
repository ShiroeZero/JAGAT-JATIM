"""JAGAT V6.5 - reclassify existing news using shared engines."""
import json
import os
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from location_engine import detect_location
from analysis_engine import analyze_article
from fetch_news import discovery_matches, POLICE_ANCHORS

NEWS_FILE = os.path.join(BASE, "data", "news.json")
ENGINE_VERSION = "normalizer-v6.5.4"


def has_any(text, terms):
    from fetch_news import contains_term
    return any(contains_term(text, term) for term in terms)


def classify_existing(item):
    title = item.get("title", "")
    summary = item.get("summary", "")
    text = f"{title} {summary}".lower()
    location = detect_location(
        title,
        source=item.get("source") or item.get("publisher") or "",
    )
    analysis = analyze_article(
        title,
        summary,
        police_context=has_any(text, POLICE_ANCHORS),
    )
    families, tags, hits = discovery_matches(text)

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
        "location_source": location.get("source") or "title",
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "category": analysis.get("classification_category") or (
            "NEGATIF - " + analysis["issue_subtype"].upper()
            if analysis.get("sentiment") == "negative"
            else "POSITIF / PENEGAKAN HUKUM"
            if analysis.get("sentiment") == "positive"
            else "NETRAL / LAINNYA"
        ),
        "scope": analysis.get("sentiment", item.get("scope", "neutral")),
        "scope_label": analysis.get("sentiment_label", item.get("scope_label", "NETRAL")),
        "issue_type": analysis["issue_type"],
        "issue_subtype": analysis["issue_subtype"],
        "issue_evidence": analysis["issue_evidence"],
        "handling_status": analysis["handling_status"],
        "handling_evidence": analysis["handling_evidence"],
        "attention_score": analysis["attention_score"],
        "attention_label": analysis["attention_label"],
        "attention_components": analysis["attention_components"],
        "attention_evidence": analysis["attention_evidence"],
        "priority": analysis["legacy_priority"],
        "discovery_families": families,
        "discovery_tags": tags,
        "discovery_hits": hits,
        "discovery_version": "discovery-v6.5.4",
    })
    return item


def main():
    with open(NEWS_FILE, encoding="utf-8") as f:
        db = json.load(f)

    items = db.get("items", [])
    db.pop("ai_case_adjudicator", None)
    db.pop("ai_case_adjudicator_version", None)
    before = json.dumps(items, ensure_ascii=False, sort_keys=True)
    for item in items:
        classify_existing(item)
    after = json.dumps(items, ensure_ascii=False, sort_keys=True)

    db["location_engine_version"] = "location-v6.5-title-only"
    db["classifier_version"] = "news-v6.5.4"
    db["analysis_engine_version"] = "analysis-v6.5.4"
    db["normalized_at"] = datetime.now(timezone.utc).isoformat()

    tmp = NEWS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NEWS_FILE)

    jatim = sum(1 for x in items if x.get("is_jatim") is True)
    outside = sum(1 for x in items if x.get("region") == "LUAR JATIM")
    unknown = sum(1 for x in items if x.get("region") == "BELUM TERPETAKAN")

    print("========================================")
    print("JAGAT NORMALISASI V6.5.3")
    print("========================================")
    print(f"News records     : {len(items)}")
    print(f"Jawa Timur       : {jatim}")
    print(f"Luar Jatim       : {outside}")
    print(f"Belum terpetakan : {unknown}")
    print(f"Changed          : {before != after}")
    print(f"Engine           : {ENGINE_VERSION}")
    print("========================================")


if __name__ == "__main__":
    main()
