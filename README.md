# Multi-Source Web Scraping Pipeline

A Python pipeline that collects books and quotes from two public practice
websites, cleans and validates the records, removes duplicates, and exports
one consolidated CSV with a summary report and execution logs.

## Environment and dependencies

Developed and tested on Windows with Python 3.13.5.

Dependencies:
- requests: downloads HTML using a reusable HTTP session.
- beautifulsoup4: extracts records and pagination links from HTML.
- lxml: parses HTML for BeautifulSoup.
- pytest: runs automated tests.

Exact installed versions are recorded in requirements.txt.

## Setup

From the project directory:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, activate with:

```bash
source venv/bin/activate
```

## Run

```bash
python main.py
```

Run tests without network access:

```bash
python -m pytest -q
```

## Sources and HTML observations

### Books to Scrape

https://books.toscrape.com/

- Record container: article.product_pod
- Title and product link: h3 > a
- Full title: the link's title attribute; visible text can be truncated.
- Price: p.price_color
- Rating: classes on p.star-rating

### Quotes to Scrape

https://quotes.toscrape.com/

- Record container: div.quote
- Quote text: span.text
- Author: small.author
- Tags: a.tag

Both websites use li.next > a for pagination. Category and description
are not extracted from book listing pages.

## Project structure

- scrapers/base_scraper.py: shared session, retries, timeout and delay.
- scrapers/books_scraper.py: book extraction and pagination.
- scrapers/quotes_scraper.py: quote extraction and pagination.
- processing/cleaning.py: reusable transformations.
- processing/validation.py: validation and rejection reasons.
- processing/deduplication.py: normalized comparison keys.
- main.py: pipeline orchestration, logging and output generation.
- tests/: processing and scraper behavior tests.
- output/: generated CSV and summary JSON.
- logs/: generated execution log.

## Data model

| Column | Books | Quotes |
| --- | --- | --- |
| source | Books to Scrape | Quotes to Scrape |
| source_url | Product URL | Listing page containing the quote |
| name_or_title | Full book title | Quote text |
| category | Empty | Empty |
| price | Numeric GBP price | Empty |
| rating | Integer from 1 to 5 | Empty |
| author | Empty | Author name |
| tags | Empty | Sorted, semicolon-separated tags |
| description | Empty | Empty |
| scraped_at | Timezone-aware UTC timestamp | Timezone-aware UTC timestamp |

Missing values are None internally and empty cells in the CSV. Prices are
in GBP; no currency conversion is performed.

## Pagination

Each scraper starts at its home page and follows the actual Next link.
Relative links are resolved using urllib.parse.urljoin. Page counts and
page URLs are not hard-coded.

Visited URLs prevent repeated-link loops. Pagination links pointing to
another host are rejected. completed is true only when a page has no
Next link; failures leave the source incomplete.

## Cleaning

- Normalize Unicode and collapse unnecessary whitespace.
- Convert empty text to None.
- Remove matching outer quotation marks from quote text.
- Convert GBP price strings into numbers.
- Convert rating words such as Three into integers.
- Normalize, deduplicate and sort tags.
- Lowercase URL scheme and host, and remove fragments.

Malformed price or rating text raises a cleaning error instead of silently
becoming an empty value. Raw dictionaries are not modified.

## Validation

Validation checks:
- Recognized source and non-empty title or quote.
- HTTP/HTTPS URL with the expected source host.
- No whitespace, credentials or unsupported ports in source URLs.
- Required book prices: finite, numeric and non-negative.
- Required book ratings: integers from 1 to 5.
- Required quote authors.
- No price or rating values on quote records.
- Valid timestamps containing a timezone.

Boolean prices and ratings are rejected. Invalid records are excluded,
logged and counted.

## Duplicate detection

Comparison keys use Unicode normalization, case folding, whitespace
normalization and consistent straight/curly quotation marks.

- Books: source + normalized title.
- Quotes: source + normalized author + full normalized quote text.

Keys are tuples stored in a set. The first occurrence is retained and
later matches are removed and counted. Original output text is preserved.

Full quote text avoids incorrectly merging quotes that share an opening.
Other punctuation is preserved to reduce accidental matches.

Limitation: title-based book matching can merge different editions or
different products with the same title. It is a documented heuristic,
not proof that the underlying products are identical.

## Reliability and logging

The shared HTTP client uses:
- A reusable requests.Session.
- An identifying User-Agent.
- A 15-second request timeout.
- A 0.5-second pause before each application-level request.
- Up to three retries with backoff for temporary failures, including
  HTTP 429, 500, 502, 503 and 504.
- Retry-After handling.

A failed page stops that source because its Next link cannot be read.
Previously collected records are retained for handled page failures.
The other source still runs.

Unexpected source exceptions are logged and isolated; records still held
inside a scraper may be lost in that case.

Missing HTML fields become missing values for validation. Pages with no
record containers stop the source as incomplete.

Logs are written to the console and logs/scraper.log. Timestamps in records
use UTC; log timestamps use the computer's local time.

## Outputs and summary accounting

Generated files:
- output/final_dataset.csv
- output/summary_report.json
- logs/scraper.log

Each run replaces these files.

The summary includes per-source page counts, completion flags, collected
and cleaned counts, rejected records, removed duplicates and final counts.
It also includes rejection reasons, run status, timestamps and duration.

Accounting:
collected = rejected + duplicates removed + final records

Cleaned counts mean cleaning succeeded, before validation. A rejected
record can have multiple reasons, so reason counts can exceed rejected
record counts.

An incomplete scrape still writes available results and exits with code 1.
A complete scrape exits with code 0. Completion refers to pagination;
rejected records are reported separately.

## Verified run

On October 6, 2026:
- Books: 50 pages, 1,000 records collected.
- Quotes: 10 pages, 100 records collected.
- Rejected records: 0.
- Title-based duplicate matches removed: 1, The Star-Touched Queen.
- Final CSV: 1,099 rows — 999 books and 100 quotes.

Saved CSV counts were checked against the JSON report. Saved records were
validated again after restoring numeric types, and no duplicates remained
under the documented rule.

Automated tests: 38 passed. Tests cover cleaning, validation, duplicate
detection, dynamic pagination, failed pages, missing fields, repeated
pagination links and external pagination links.

Actual counts may change if the websites change.

The setup was also reproduced successfully in a fresh virtual environment:
dependencies installed from requirements.txt, pip check passed, all
38 tests passed, and the complete pipeline produced matching output counts.

## Assumptions and limitations

- The websites retain their current server-rendered HTML structures.
- Book category and description remain empty because detail pages are
  not visited.
- Quote source URLs identify listing pages, not individual quote URLs.
- Matching is normalized key equality, not fuzzy semantic matching.
- No database, checkpoint/resume mechanism or asynchronous scraping.
- Automated tests simulate page failures; they do not verify every
  live network or retry condition.
- The implementation does not automatically inspect robots.txt;
  applicable site restrictions should be checked before use.
- Compatibility with Python versions other than 3.13.5 is not claimed.

## AI usage

ChatGPT assisted with implementation, explanations, tests and documentation.
See AI_USAGE.md for details. The candidate is responsible for reviewing
and understanding the submitted solution.

## Browser dashboard

The optional Streamlit dashboard displays saved pipeline results,
supports source filtering and text search, and provides CSV and JSON
downloads. It does not run live scraping.

Run locally:
python -m streamlit run app.py