import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from processing.cleaning import clean_record
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.base_scraper import HTTPClient
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper


BASE_DIR = Path(__file__).resolve().parent

FIELDS = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "scraped_at",
]


def main():
    output_dir = BASE_DIR / "output"
    logs_dir = BASE_DIR / "logs"

    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(
                logs_dir / "scraper.log",
                mode="w",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )

    logger = logging.getLogger(__name__)
    started_at = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()

    raw_records = []
    source_stats = {}
    client = HTTPClient()

    try:
        for scraper_class in (BooksScraper, QuotesScraper):
            scraper = scraper_class(client)
            source = scraper.SOURCE

            source_stats[source] = {
                "pages_scraped": 0,
                "completed": False,
                "collected": 0,
                "cleaned": 0,
                "rejected": 0,
                "duplicates_removed": 0,
                "final_count": 0,
            }

            try:
                records = scraper.scrape()
                raw_records.extend(records)

                source_stats[source].update({
                    "pages_scraped": scraper.pages_scraped,
                    "completed": scraper.completed,
                    "collected": len(records),
                })

                logger.info(
                    "%s: collected %d records; completed=%s",
                    source,
                    len(records),
                    scraper.completed,
                )
            except Exception:
                # Isolate an unexpected source failure so the other runs.
                source_stats[source]["pages_scraped"] = scraper.pages_scraped
                logger.exception("Unexpected failure in %s", source)
    finally:
        client.close()

    valid_records = []
    rejected_by_reason = Counter()

    for raw_record in raw_records:
        source = raw_record["source"]

        try:
            cleaned = clean_record(raw_record)
        except (ValueError, TypeError, OverflowError) as exc:
            source_stats[source]["rejected"] += 1
            rejected_by_reason["cleaning_error"] += 1

            logger.warning(
                "Cleaning rejected %s: %s",
                raw_record.get("source_url"),
                exc,
            )
            continue

        source_stats[source]["cleaned"] += 1
        problems = validate_record(cleaned)

        if problems:
            source_stats[source]["rejected"] += 1
            rejected_by_reason.update(problems)

            logger.warning(
                "Validation rejected %s: %s",
                cleaned.get("source_url"),
                ", ".join(problems),
            )
            continue

        valid_records.append(cleaned)

    unique_records, duplicates = find_duplicates(valid_records)

    for record in duplicates:
        source_stats[record["source"]]["duplicates_removed"] += 1
        logger.info("Duplicate removed: %s", record["name_or_title"])

    for record in unique_records:
        source_stats[record["source"]]["final_count"] += 1

    csv_path = output_dir / "final_dataset.csv"

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(unique_records)

    collected = len(raw_records)
    cleaned_count = sum(item["cleaned"] for item in source_stats.values())
    rejected_count = sum(item["rejected"] for item in source_stats.values())

    # Every collected record must be accounted for.
    assert collected == rejected_count + len(duplicates) + len(unique_records)

    run_complete = all(item["completed"] for item in source_stats.values())

    summary = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.perf_counter() - start_time, 3),
        "status": "complete" if run_complete else "incomplete",
        "sources": source_stats,
        "total_collected": collected,
        "total_after_cleaning": cleaned_count,
        "total_rejected": rejected_count,
        "rejected_by_reason": dict(rejected_by_reason),
        "duplicates_removed": len(duplicates),
        "final_record_count": len(unique_records),
    }

    summary_path = output_dir / "summary_report.json"

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    logger.info(
        "Run %s: collected=%d rejected=%d duplicates=%d final=%d",
        summary["status"],
        collected,
        rejected_count,
        len(duplicates),
        len(unique_records),
    )

    print("\nRun status:", summary["status"])
    print("Collected:", collected)
    print("Rejected:", rejected_count)
    print("Duplicates removed:", len(duplicates))
    print("Final records:", len(unique_records))
    print("CSV:", csv_path)
    print("Summary:", summary_path)
    print("Log:", logs_dir / "scraper.log")

    return 0 if run_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())