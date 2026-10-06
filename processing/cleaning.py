import math
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def clean_text(value):
    """Normalize Unicode and whitespace; return None for empty text."""
    if value is None:
        return None

    text = unicodedata.normalize("NFC", str(value))
    return " ".join(text.split()) or None


def strip_quotes(value):
    """Remove matching outer quote marks without changing inner text."""
    text = clean_text(value)

    if text is None:
        return None

    pairs = {
        "“": "”",
        '"': '"',
    }

    if len(text) >= 2 and pairs.get(text[0]) == text[-1]:
        text = text[1:-1]

    return clean_text(text)


def clean_price(value):
    """Convert a GBP price string into a number."""
    text = clean_text(value)

    if text is None:
        return None

    text = text.removeprefix("£").strip()

    pattern = r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?"

    if not re.fullmatch(pattern, text):
        raise ValueError(f"Invalid price: {value!r}")

    price = float(text.replace(",", ""))

    if not math.isfinite(price):
        raise ValueError(f"Non-finite price: {value!r}")

    return price


def clean_rating(value):
    """Convert a Books to Scrape rating class into an integer."""
    text = clean_text(value)

    if text is None:
        return None

    words = text.casefold().split()
    ratings = [RATING_MAP[word] for word in words if word in RATING_MAP]

    if len(ratings) != 1:
        raise ValueError(f"Invalid rating: {value!r}")

    return ratings[0]


def clean_tags(values):
    """Normalize, deduplicate, and sort tags for a CSV cell."""
    if not values:
        return None

    tags = set()

    for value in values:
        tag = clean_text(value)

        if tag:
            tags.add(tag.casefold())

    return ";".join(sorted(tags)) or None


def normalize_url(value):
    """Normalize URL scheme and host, preserving path and query."""
    text = clean_text(value)

    if text is None:
        return None

    parts = urlsplit(text)

    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path,
        parts.query,
        "",  # Remove the fragment; it is not sent to the server.
    ))


def clean_record(record):
    """Return a cleaned copy, leaving the original record unchanged."""
    cleaned = dict(record)

    text_fields = [
        "source",
        "name_or_title",
        "category",
        "author",
        "description",
        "scraped_at",
    ]

    for field in text_fields:
        cleaned[field] = clean_text(record.get(field))

    if cleaned["source"] == "Quotes to Scrape":
        cleaned["name_or_title"] = strip_quotes(
            cleaned["name_or_title"]
        )

    cleaned["price"] = clean_price(record.get("price"))
    cleaned["rating"] = clean_rating(record.get("rating"))
    cleaned["tags"] = clean_tags(record.get("tags"))
    cleaned["source_url"] = normalize_url(record.get("source_url"))

    return cleaned