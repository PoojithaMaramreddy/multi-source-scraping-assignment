import logging
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BooksScraper:
    SOURCE = "Books to Scrape"
    START_URL = "https://books.toscrape.com/"

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
                logger.error("Books source stopped at failed page: %s", url)
                break

            soup = BeautifulSoup(html, "lxml")
            articles = soup.select("article.product_pod")

            if not articles:
                logger.error("No book containers found on %s", url)
                break

            scraped_at = datetime.now(timezone.utc).isoformat()

            for article in articles:
                link = article.select_one("h3 > a")
                price = article.select_one("p.price_color")
                rating = article.select_one("p.star-rating")

                href = link.get("href") if link else None

                records.append({
                    "source": self.SOURCE,
                    "source_url": urljoin(url, href) if href else None,
                    "name_or_title": (
                        link.get("title") or link.get_text()
                    ) if link else None,
                    "category": None,
                    "price": price.get_text() if price else None,
                    "rating": (
                        " ".join(rating.get("class", []))
                    ) if rating else None,
                    "author": None,
                    "tags": None,
                    "description": None,
                    "scraped_at": scraped_at,
                })

            self.pages_scraped += 1

            logger.info(
                "Books page %d: collected %d records",
                self.pages_scraped,
                len(articles),
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