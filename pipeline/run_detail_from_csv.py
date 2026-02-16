import csv
import json
import os
from crawling.raw_detail import scrape_listing

INPUT_CSV = "data/listing.csv"
OUTPUT_JSONL = "data/detail_output.jsonl"


def load_scraped_urls():
    scraped = set()

    if not os.path.exists(OUTPUT_JSONL):
        return scraped

    with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                scraped.add(record.get("url"))
            except:
                continue

    return scraped


def run():
    scraped_urls = load_scraped_urls()
    print(f"Already scraped: {len(scraped_urls)}")

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            url = row["url"]
            if url in scraped_urls:
                print(f"Skip: {url}")
                continue
            print(f"Scraping: {url}")

            try:
                data = scrape_listing(url, headless=False)

                with open(OUTPUT_JSONL, "a", encoding="utf-8") as out:
                    out.write(json.dumps(data, ensure_ascii=False) + "\n")

            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    run()
