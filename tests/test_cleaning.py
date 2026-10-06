import pytest

from processing.cleaning import (
    clean_text,
    strip_quotes,
    clean_price,
    clean_rating,
    clean_tags,
)


def test_whitespace_and_missing_text():
    assert clean_text("  Hello \n World\u00a0 ") == "Hello World"
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_quote_marks():
    assert strip_quotes("\u201cExample quote.\u201d") == "Example quote."
    assert strip_quotes("Don't change inner punctuation.") == (
        "Don't change inner punctuation."
    )


def test_price_conversion():
    assert clean_price("\u00a351.77") == 51.77
    assert clean_price("\u00a31,234.50") == 1234.50
    assert clean_price(None) is None


@pytest.mark.parametrize("value", ["unknown", "price 51", "12,34", "NaN"])
def test_malformed_prices_are_rejected(value):
    with pytest.raises(ValueError):
        clean_price(value)


def test_rating_conversion():
    assert clean_rating("star-rating Three") == 3

    with pytest.raises(ValueError):
        clean_rating("star-rating Unknown")


def test_tags_are_normalized():
    assert clean_tags(["World", "thinking", "world", " "]) == "thinking;world"
    assert clean_tags([]) is None