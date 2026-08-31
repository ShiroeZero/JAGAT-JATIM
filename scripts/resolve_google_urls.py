"""Resolve Google News redirect URLs into original publisher URLs.

Google News RSS exposes article links under news.google.com/rss/articles/... .
JAGAT keeps that URL as google_news_url for provenance, while url is replaced
with the decoded publisher URL when resolution succeeds. Failed resolutions
remain usable through the Google URL fallback.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

OUT = Path("data/news.json")
MAX_RESOLVE_PER_RUN = int(os.environ.get("JAGAT_URL_RESOLVE_LIMIT", "60"))
INTERVAL_SECONDS = float(os.environ.get("JAGAT_URL_RESOLVE_INTERVAL", "1"))


def is_google_news_url(value: str | None) -> bool:
    value = str(value or "").strip().lower()
    return value.startswith("https://news.google.com/") and "/rss/articles/" in value or value.startswith("https://news.google.com/read/")


def resolve(url: str) -> str | None:
    try:
        from googlenewsdecoder import gnewsdecoder
    except Exception as exc:
        print(f"WARN: googlenewsdecoder belum tersedia: {exc}")
        return None

    try:
        result = gnewsdecoder(url, interval=INTERVAL_SECONDS)
        if isinstance(result, dict) and result.get("status"):
            decoded = str(result.get("decoded_url") or "").strip()
            if decoded and not is_google_news_url(decoded):
                return decoded
    except Exception as exc:
        print(f"WARN: gagal resolve URL: {exc}")
    return None


def main() -> None:
    if not OUT.exists():
        print("URL resolver: data/news.json belum ada")
        return

    data = json.loads(OUT.read_text(encoding="utf-8"))
    items = data.get("items", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        print("URL resolver: format items tidak valid")
        return

    # Prefer newest articles first. Older Google URLs are backfilled gradually.
    candidates = []
    for item in items:
        if not isinstance(item, dict):
            continue
        current = str(item.get("url") or "").strip()
        original = str(item.get("original_url") or "").strip()
        google_url = str(item.get("google_news_url") or "").strip()
        if google_url and original:
            continue
        target = google_url or current
        if is_google_news_url(target):
            candidates.append(item)

    candidates.sort(key=lambda x: str(x.get("published_at") or ""), reverse=True)
    candidates = candidates[:MAX_RESOLVE_PER_RUN]

    attempted = resolved = 0
    changed = False
    for item in candidates:
        current = str(item.get("url") or "").strip()
        google_url = str(item.get("google_news_url") or "").strip() or current
        decoded = resolve(google_url)
        attempted += 1
        if decoded:
            item["google_news_url"] = google_url
            item["original_url"] = decoded
            item["url"] = decoded
            resolved += 1
            changed = True
        time.sleep(INTERVAL_SECONDS)

    data["url_resolution_version"] = "google-news-original-v1"
    data["url_resolution_stats"] = {
        "attempted": attempted,
        "resolved": resolved,
        "remaining_google_urls": sum(
            1 for x in items
            if isinstance(x, dict) and is_google_news_url(x.get("url"))
        ),
    }
    if changed:
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("========================================")
    print("JAGAT ORIGINAL URL RESOLVER")
    print("========================================")
    print(f"Attempted : {attempted}")
    print(f"Resolved  : {resolved}")
    print(f"Remaining : {data['url_resolution_stats']['remaining_google_urls']}")
    print("========================================")


if __name__ == "__main__":
    main()
