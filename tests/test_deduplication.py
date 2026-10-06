from processing.deduplication import find_duplicates


def test_books_ignore_case_and_whitespace():
    records = [
        {"source": "Books to Scrape", "name_or_title": "Example Book"},
        {"source": "Books to Scrape", "name_or_title": " example   BOOK "},
        {"source": "Books to Scrape", "name_or_title": "Different Book"},
    ]

    unique, duplicates = find_duplicates(records)

    assert len(unique) == 2
    assert len(duplicates) == 1
    assert unique[0] is records[0]


def test_quotes_compare_full_text():
    prefix = "A shared opening that is deliberately longer than fifty characters. "
    base = {"source": "Quotes to Scrape", "author": "Example Author"}

    records = [
        {**base, "name_or_title": prefix + "First ending."},
        {**base, "name_or_title": prefix + "Different ending."},
        {
            **base,
            "author": " example AUTHOR ",
            "name_or_title": (prefix + "First ending.").upper(),
        },
    ]

    unique, duplicates = find_duplicates(records)

    assert len(unique) == 2
    assert len(duplicates) == 1


def test_same_quote_with_different_authors_is_preserved():
    records = [
        {
            "source": "Quotes to Scrape",
            "author": author,
            "name_or_title": "Same text.",
        }
        for author in ["Author A", "Author B"]
    ]

    unique, duplicates = find_duplicates(records)

    assert len(unique) == 2
    assert not duplicates


def test_straight_and_curly_apostrophes_match():
    base = {"source": "Books to Scrape"}

    records = [
        {**base, "name_or_title": "Author's Book"},
        {**base, "name_or_title": "Author\u2019s Book"},
    ]

    unique, duplicates = find_duplicates(records)

    assert len(unique) == 1
    assert len(duplicates) == 1
