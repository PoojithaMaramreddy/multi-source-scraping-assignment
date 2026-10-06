import math
from datetime import datetime
from urllib.parse import urlsplit


SOURCE_HOSTS = {
    "Books to Scrape": "books.toscrape.com",
    "Quotes to Scrape": "quotes.toscrape.com",
}


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_record(record):
    """Return rejection reasons; an empty list means valid."""
    problems = []
    source = record.get("source")

    if source not in SOURCE_HOSTS:
        problems.append("unknown_source")

    if not has_text(record.get("name_or_title")):
        problems.append("missing_name")

    url = record.get("source_url")

    try:
        if not isinstance(url, str) or not url:
            raise ValueError("Missing URL")

        parts = urlsplit(url)

        # Accessing port also checks for malformed port numbers.
        port = parts.port

        if (
            parts.scheme not in ("http", "https")
            or not parts.hostname
            or any(character.isspace() for character in url)
            or parts.username is not None
            or parts.password is not None
            or port not in (None, 80, 443)
        ):
            raise ValueError("Invalid URL")

        if (
            source in SOURCE_HOSTS
            and parts.hostname != SOURCE_HOSTS[source]
        ):
            problems.append("wrong_source_host")

    except (ValueError, TypeError):
        problems.append("invalid_url")

    price = record.get("price")

    if price is None:
        if source == "Books to Scrape":
            problems.append("missing_price")
    elif (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(price)
        or price < 0
    ):
        problems.append("invalid_price")

    rating = record.get("rating")

    if rating is None:
        if source == "Books to Scrape":
            problems.append("missing_rating")
    elif type(rating) is not int or not 1 <= rating <= 5:
        problems.append("invalid_rating")

    if source == "Quotes to Scrape":
        if not has_text(record.get("author")):
            problems.append("missing_author")

        if price is not None or rating is not None:
            problems.append("unexpected_quote_numeric_fields")

    timestamp = record.get("scraped_at")

    try:
        parsed = datetime.fromisoformat(timestamp)

        if parsed.utcoffset() is None:
            raise ValueError("Timestamp needs a timezone")

    except (ValueError, TypeError):
        problems.append("invalid_timestamp")

    return problems