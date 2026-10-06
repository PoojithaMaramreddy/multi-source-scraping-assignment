import logging
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class QuotesScraper:
    SOURCE = "Quotes to Scrape"
    START_URL = "https://quotes.toscrape.com/"

    def __init__(self, client):
        self.client = client
        self.pages_scraped = 0
        self.completed = False

    def scrape(self):
        records = []
        visited = set()
        url = self.START_URL

        self.pages_scraped = 0
        self.completed = False

        while url:
            if url in visited:
                logger.error("Repeated page URL; stopping: %s", url)
                break

            visited.add(url)
            html = self.client.get_html(url)

            if html is None:
                logger.error("Quotes source stopped at failed page: %s", url)
                break

            soup = BeautifulSoup(html, "lxml")
            quotes = soup.select("div.quote")

            if not quotes:
                logger.error("No quote containers found on %s", url)
                break

            scraped_at = datetime.now(timezone.utc).isoformat()

            for quote in quotes:
                text = quote.select_one("span.text")
                author = quote.select_one("small.author")
                tags = quote.select("a.tag")

                records.append({
                    "source": self.SOURCE,
                    "source_url": url,
                    "name_or_title": text.get_text() if text else None,
                    "category": None,
                    "price": None,
                    "rating": None,
                    "author": author.get_text() if author else None,
                    "tags": [tag.get_text() for tag in tags],
                    "description": None,
                    "scraped_at": scraped_at,
                })

            self.pages_scraped += 1

            logger.info(
                "Quotes page %d: collected %d records",
                self.pages_scraped,
                len(quotes),
            )

            next_link = soup.select_one("li.next > a")

            if next_link is None:
                self.completed = True
                break

            next_href = next_link.get("href")

            if not next_href:
                logger.error("Next link has no URL on %s", url)
                break

            next_url = urljoin(url, next_href)

            if (
                urlsplit(next_url).hostname
                != urlsplit(self.START_URL).hostname
            ):
                logger.error("Unexpected pagination host: %s", next_url)
                break

            url = next_url

        return records
