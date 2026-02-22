import csv
import json
import os

from crawling.raw_detail import scrape_listing
from pipeline.resources.MinioIO import MinIOClient

INPUT_CSV = "data/listing.csv"
BATCH_SIZE = 20


CHECKPOINT_FILE = "checkpoint/detail_from_csv_checkpoint.txt"
BATCH_SIZE = 100


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return 0
    with open(CHECKPOINT_FILE, "r") as f:
        return int(f.read().strip())


def save_checkpoint(index):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(index))
        
def run():
    minio_client = MinIOClient()

    batch = []
    start_index = load_checkpoint()
    print(f"Resume from index: {start_index}")

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):

            if i < start_index:
                continue

            url = row["url"]
            print(f"[{i}] Scraping: {url}")

            try:
                data = scrape_listing(url, headless=False)
                batch.append(data)

                if len(batch) >= BATCH_SIZE:
                    minio_client.upload_json_batch(batch)
                    save_checkpoint(i + 1)
                    batch.clear()

            except Exception as e:
                print(f"Error: {e}")

    if batch:
        minio_client.upload_json_batch(batch)
        save_checkpoint(i + 1)

    print("Done.")


if __name__ == "__main__":
    run()