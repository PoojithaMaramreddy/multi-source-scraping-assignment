import csv
import json
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

st.set_page_config(
    page_title="Multi-Source Scraping Dashboard",
    page_icon="📚",
    layout="wide",
)

st.title("Multi-Source Scraping Dashboard")
st.write(
    "Explore the cleaned book and quote records produced "
    "by the Python scraping pipeline."
)
st.caption(
    "This dashboard displays the saved dataset. "
    "Run python main.py locally to collect fresh data."
)

csv_path = OUTPUT_DIR / "final_dataset.csv"
summary_path = OUTPUT_DIR / "summary_report.json"

if not csv_path.exists() or not summary_path.exists():
    st.error("Output files are missing. Run python main.py first.")
    st.stop()

with csv_path.open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))

with summary_path.open(encoding="utf-8") as file:
    summary = json.load(file)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Collected", summary["total_collected"])
col2.metric("Rejected", summary["total_rejected"])
col3.metric("Duplicates removed", summary["duplicates_removed"])
col4.metric("Final records", summary["final_record_count"])

st.caption(
    f"Run status: {summary['status']} | "
    f"Finished at: {summary['finished_at']}"
)

source = st.selectbox(
    "Choose a source",
    ["All sources"] + sorted({row["source"] for row in rows}),
)

search = st.text_input("Search titles, quotes, or authors")

filtered = [
    row
    for row in rows
    if (
        source == "All sources"
        or row["source"] == source
    )
    and (
        not search.strip()
        or search.strip().casefold()
        in (
            row["name_or_title"] + " " + row["author"]
        ).casefold()
    )
]

st.write(f"Showing {len(filtered)} records")

# Restore numeric types for display; CSV values are strings.
display_rows = []

for row in filtered:
    display_row = dict(row)
    display_row["price"] = (
        float(row["price"]) if row["price"] else None
    )
    display_row["rating"] = (
        int(row["rating"]) if row["rating"] else None
    )
    display_rows.append(display_row)

if display_rows:
    st.dataframe(display_rows, use_container_width=True)
else:
    st.info("No records match your filters.")

st.subheader("Download pipeline outputs")

st.download_button(
    "Download full dataset CSV",
    data=csv_path.read_bytes(),
    file_name="final_dataset.csv",
    mime="text/csv",
)

st.download_button(
    "Download summary JSON",
    data=summary_path.read_bytes(),
    file_name="summary_report.json",
    mime="application/json",
)

with st.expander("View summary report"):
    st.json(summary)

with st.expander("Method and limitations"):
    st.write(
        "Records are scraped using Requests and BeautifulSoup, "
        "cleaned, validated, and deduplicated before export. "
        "Book duplicates are identified by normalized title. "
        "Quote duplicates use normalized author and full quote text."
    )
    st.write(
        "Title-based book matching can merge different editions. "
        "Book category and description are not collected."
    )

st.markdown(
    "[View source code on GitHub]"
    "(https://github.com/PoojithaMaramreddy/"
    "multi-source-scraping-assignment)"
)