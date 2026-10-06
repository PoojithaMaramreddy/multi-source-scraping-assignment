# AI Usage

## Tool used

ChatGPT.

## How it was used

ChatGPT assisted with:
- Interpreting the assignment and planning implementation stages.
- Explaining Requests, BeautifulSoup, lxml and pytest.
- Generating the shared HTTP helper and both source scrapers.
- Designing cleaning, validation and deduplication functions.
- Creating main.py, output accounting and logging.
- Generating automated tests and verification commands.
- Troubleshooting terminal errors.
- Drafting documentation and Git commands.

All main implementation modules and tests were AI-assisted.

## Representative prompts

Actual prompts used during the conversation included:
- "so what is our first step....."
- "step by step"
- "wait explain what we did exactly everytime... y beautiful soup like that"
- "what code should be pasted in books_scraper.py"
- "what we completed what is remaining"
- "bro... what about git?? should we do??"

Execution output and errors were shared with ChatGPT to guide debugging
and the next implementation steps.

## Decisions and corrections during the workflow

- Used the full quote text and author for duplicate detection instead
  of the reference guide's suggested first 50 quote characters.
- Used tuple keys and a set rather than manually hashing the keys.
- Preserved most punctuation while normalizing straight/curly quotation
  marks, capitalization, Unicode and whitespace.
- Rejected malformed prices explicitly instead of extracting an arbitrary
  number from otherwise invalid text.
- Added source-host checks, repeated pagination protection, and explicit
  incomplete-run reporting.
- Kept book category and description empty rather than inventing values.

## Issues and limitations identified

A PowerShell test piped literal Unicode characters into Python as question
marks. This changed the pound symbol and curly quotes in test input.
The test was corrected using Unicode escapes. Website responses already
preserved these characters correctly.

The real run found one title-based duplicate match, The Star-Touched Queen.
Matching titles do not prove identical products or editions. This
limitation is documented in the README.

An initial main.py execution failed because the file was not available at
the expected project-root path. After correcting the file setup, the full
pipeline ran successfully.

Some proposed approaches were improved during guidance rather than through
independent candidate refactoring. AI assistance is disclosed accordingly.

## Verification performed

- Confirmed package imports in the virtual environment.
- Tested access to both source websites.
- Ran the Books scraper: 50 pages and 1,000 records.
- Ran the Quotes scraper: 10 pages and 100 records.
- Checked sample cleaning and validation cases.
- Tested deliberately duplicated book and quote records.
- Ran the complete pipeline: 1,100 collected, 0 rejected,
  1 duplicate match removed, and 1,099 final records.
- Read the saved CSV and compared its counts with the summary JSON.
- Revalidated saved records after restoring numeric types.
- Confirmed no remaining duplicates under the documented rule.
- Confirmed the execution log exists and contains data.
- Ran automated processing and scraper tests: 38 passed.

Automated scraper tests use fake HTML responses and make no network
requests. Live retry conditions have not all been tested.

A second virtual environment was created and dependencies were installed
from requirements.txt. pip check reported no broken requirements, all
38 tests passed, and the complete pipeline ran successfully. The resulting
CSV contained 1,099 records, and its counts matched the summary report.

ChatGPT assisted with the Streamlit dashboard and deployment guidance.
Local checks confirmed the table, source filters, text search, no-match
message, and CSV/JSON downloads worked.