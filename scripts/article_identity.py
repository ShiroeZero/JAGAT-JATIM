"""Canonical URL identity and non-destructive duplicate annotation.

Original records and source URLs are retained. URL equality is recorded as
article-level duplicate metadata; it never merges case clusters or deletes rows.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "gclid", "dclid", "fbclid", "mc_cid", "mc_eid", "ocid",
    "ref", "ref_src", "source", "cmpid",
}


def canonical_article_url(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
        scheme = (parts.scheme or "https").lower()
        host = (parts.hostname or "").lower()
        if not host:
            return raw.rstrip("/")
        if host.startswith("www."):
            host = host[4:]
        port = parts.port
        netloc = host
        if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
            netloc = f"{host}:{port}"
        path = re.sub(r"/{2,}", "/", parts.path or "/")
        if path != "/":
            path = path.rstrip("/")
        query = [
            (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in TRACKING_PARAMS
        ]
        query.sort()
        return urlunsplit((scheme, netloc, path, urlencode(query, doseq=True), ""))
    except (ValueError, TypeError):
        return raw.rstrip("/")


def _article_url(item: dict) -> str:
    return canonical_article_url(item.get("original_url") or item.get("url"))


def annotate_duplicate_articles(items: list[dict]) -> dict:
    """Annotate duplicate publisher URLs without deleting or merging records."""
    groups: dict[str, list[dict]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        canonical = _article_url(item)
        if not canonical:
            item.pop("canonical_url", None)
            continue
        item["canonical_url"] = canonical
        groups.setdefault(canonical, []).append(item)

    duplicate_groups = 0
    duplicate_records = 0
    for canonical, group in groups.items():
        if len(group) < 2:
            for item in group:
                item["duplicate_article"] = False
                item.pop("duplicate_of_id", None)
                item.pop("duplicate_group_id", None)
            continue
        duplicate_groups += 1
        group_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        primary = group[0]
        primary["duplicate_article"] = False
        primary["duplicate_group_id"] = group_id
        primary.pop("duplicate_of_id", None)
        primary_id = str(primary.get("id") or "").strip()
        for item in group[1:]:
            item["duplicate_article"] = True
            item["duplicate_group_id"] = group_id
            if primary_id:
                item["duplicate_of_id"] = primary_id
            else:
                item.pop("duplicate_of_id", None)
            duplicate_records += 1
    return {
        "canonical_url_groups": len(groups),
        "duplicate_groups": duplicate_groups,
        "duplicate_records": duplicate_records,
        "records_preserved": len(items),
    }
