"""Regression tests for canonical article URL identity."""
from article_identity import canonical_article_url, annotate_duplicate_articles


def test_url_normalization():
    assert canonical_article_url("HTTPS://WWW.Example.com/news/story/?utm_source=x#section") == "https://example.com/news/story"
    assert canonical_article_url("https://example.com/story?b=2&a=1") == "https://example.com/story?a=1&b=2"
    assert canonical_article_url("") == ""


def test_duplicate_annotation_preserves_records():
    items = [
        {"id": "a", "url": "https://www.example.com/story/?utm_source=x", "title": "First"},
        {"id": "b", "url": "https://example.com/story", "title": "Second"},
        {"id": "c", "url": "https://example.com/other", "title": "Third"},
    ]
    stats = annotate_duplicate_articles(items)
    assert len(items) == 3
    assert stats["duplicate_groups"] == 1
    assert stats["duplicate_records"] == 1
    assert items[0]["duplicate_article"] is False
    assert items[1]["duplicate_article"] is True
    assert items[1]["duplicate_of_id"] == "a"
    assert items[0]["canonical_url"] == items[1]["canonical_url"]
    assert "duplicate_of_id" not in items[2]


if __name__ == "__main__":
    test_url_normalization()
    test_duplicate_annotation_preserves_records()
    print("ARTICLE IDENTITY REGRESSION TESTS: OK")
