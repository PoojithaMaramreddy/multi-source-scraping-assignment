import pytest

from processing.validation import validate_record


def valid_book():
    return {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/example/index.html",
        "name_or_title": "Example Book",
        "price": 51.77,
        "rating": 3,
        "author": None,
        "scraped_at": "2026-10-06T16:45:00+00:00",
    }


def test_valid_book():
    assert validate_record(valid_book()) == []


@pytest.mark.parametrize("price", [-1, float("nan"), float("inf"), True])
def test_invalid_prices(price):
    record = {**valid_book(), "price": price}
    assert "invalid_price" in validate_record(record)


@pytest.mark.parametrize("rating", [0, 6, 3.0, True])
def test_invalid_ratings(rating):
    record = {**valid_book(), "rating": rating}
    assert "invalid_rating" in validate_record(record)


def test_missing_book_fields():
    record = {**valid_book(), "price": None, "rating": None}
    problems = validate_record(record)

    assert "missing_price" in problems
    assert "missing_rating" in problems


@pytest.mark.parametrize("url", ["https://", "not-a-url", "https://example.com/"])
def test_invalid_or_wrong_host(url):
    record = {**valid_book(), "source_url": url}
    assert validate_record(record)


def test_quote_requires_author():
    record = {
        **valid_book(),
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com/",
        "price": None,
        "rating": None,
        "author": None,
    }

    assert "missing_author" in validate_record(record)


def test_timestamp_requires_timezone():
    record = {
        **valid_book(),
        "scraped_at": "2026-10-06T16:45:00",
    }

    assert "invalid_timestamp" in validate_record(record)