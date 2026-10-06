import unicodedata

from processing.cleaning import clean_text


PUNCTUATION_MAP = str.maketrans({
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
})


def normalize_key(value):
    """Normalize text for comparison without changing output values."""
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = text.translate(PUNCTUATION_MAP)

    return (clean_text(text) or "").casefold()


def make_fingerprint(record):
    """Return a tuple of identifying fields."""
    source = record["source"]

    if source == "Books to Scrape":
        return (
            source,
            normalize_key(record.get("name_or_title")),
        )

    if source == "Quotes to Scrape":
        return (
            source,
            normalize_key(record.get("author")),
            normalize_key(record.get("name_or_title")),
        )

    raise ValueError(f"Unknown source: {source!r}")


def find_duplicates(records):
    """Keep the first occurrence and collect later duplicates."""
    seen = set()
    unique = []
    duplicates = []

    for record in records:
        fingerprint = make_fingerprint(record)

        if fingerprint in seen:
            duplicates.append(record)
        else:
            seen.add(fingerprint)
            unique.append(record)

    return unique, duplicates