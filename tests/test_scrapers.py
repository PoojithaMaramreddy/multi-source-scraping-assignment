import pytest

from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper


BOOK_HTML = """
<article class="product_pod">
    <h3>
        <a href="/catalogue/example/index.html" title="Example Book">
            Example...
        </a>
    </h3>
    <p class="price_color">&#163;12.50</p>
    <p class="star-rating Three"></p>
</article>
"""

QUOTE_HTML = """
<div class="quote">
    <span class="text">Example quote.</span>
    <small class="author">Example Author</small>
    <a class="tag">example</a>
</div>
"""


class FakeClient:
    """Return predefined HTML instead of making network requests."""

    def __init__(self, pages):
        self.pages = pages
        self.requested = []

    def get_html(self, url):
        self.requested.append(url)
        return self.pages.get(url)


@pytest.fixture(params=[
    (BooksScraper, BOOK_HTML),
    (QuotesScraper, QUOTE_HTML),
])
def source(request):
    return request.param


def test_follows_next_link(source):
    scraper_class, html = source
    start = scraper_class.START_URL
    next_url = start + "second-page"

    client = FakeClient({
        start: html + '<li class="next"><a href="/second-page">Next</a></li>',
        next_url: html,
    })

    scraper = scraper_class(client)
    records = scraper.scrape()

    assert client.requested == [start, next_url]
    assert len(records) == 2
    assert scraper.pages_scraped == 2
    assert scraper.completed is True


def test_failed_page_preserves_previous_records(source):
    scraper_class, html = source
    start = scraper_class.START_URL

    client = FakeClient({
        start: html + '<li class="next"><a href="/failed-page">Next</a></li>',
        start + "failed-page": None,
    })

    scraper = scraper_class(client)
    records = scraper.scrape()

    assert len(records) == 1
    assert scraper.pages_scraped == 1
    assert scraper.completed is False


def test_repeated_next_link_stops_loop(source):
    scraper_class, html = source
    start = scraper_class.START_URL

    client = FakeClient({
        start: html + '<li class="next"><a href="/">Next</a></li>',
    })

    scraper = scraper_class(client)
    records = scraper.scrape()

    assert len(records) == 1
    assert client.requested == [start]
    assert scraper.completed is False


def test_missing_fields_do_not_crash(source):
    scraper_class, _ = source

    html = (
        '<article class="product_pod"></article>'
        if scraper_class is BooksScraper
        else '<div class="quote"></div>'
    )

    client = FakeClient({scraper_class.START_URL: html})
    scraper = scraper_class(client)
    records = scraper.scrape()

    assert len(records) == 1
    assert records[0]["name_or_title"] is None
    assert scraper.completed is True


def test_external_next_link_is_not_requested(source):
    scraper_class, html = source
    start = scraper_class.START_URL

    client = FakeClient({
        start: html + (
            '<li class="next">'
            '<a href="https://example.com/">Next</a>'
            '</li>'
        ),
    })

    scraper = scraper_class(client)
    scraper.scrape()

    assert client.requested == [start]
    assert scraper.completed is False