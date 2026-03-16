import os
import csv
import time
from datetime import datetime, timezone
from tqdm import tqdm
from pyvirtualdisplay import Display # pip install pyvirtualdisplay

from crawling.raw_listing_page import (
    ensure_dirs,
    setup_logger,
    init_driver,
    crawl_page
)

DATA_DIR = "data"

CSV_MASTER = f"{DATA_DIR}/listing.csv"
CSV_NEW = f"{DATA_DIR}/listing_new.csv"

MAX_PAGE_DAILY = 10


def init_new_csv():

    if not os.path.exists(CSV_NEW):

        with open(CSV_NEW, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["listing_id", "url", "crawl_time"])


def append_listing_new(listing_id, url):

    crawl_time = datetime.now(timezone.utc).isoformat()

    with open(CSV_NEW, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)
        writer.writerow([listing_id, url, crawl_time])


def load_existing_ids():

    ids = set()

    if not os.path.exists(CSV_MASTER):
        return ids

    with open(CSV_MASTER, "r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:
            ids.add(row["listing_id"])

    return ids


def crawl_page_daily(driver, page, existing_ids):

    from crawling.raw_listing_page import build_page_url
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    WAIT_TIMEOUT = 15

    url = build_page_url(page)

    print(f"Crawling page {page}: {url}")

    driver.get(url)

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a.js__product-link-for-product-id")
            )
        )

    except:
        print("No listings found")
        return 0

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "a.js__product-link-for-product-id"
    )

    new_count = 0

    for el in elements:

        listing_id = el.get_attribute("data-product-id")
        href = el.get_attribute("href")

        if not listing_id or not href:
            continue

        if listing_id in existing_ids:
            continue

        append_listing_new(listing_id, href)

        existing_ids.add(listing_id)
        new_count += 1

    print(f"Page {page} | New listings: {new_count}")

    return new_count


def main():

    ensure_dirs()
    setup_logger()
    init_new_csv()

    existing_ids = load_existing_ids()

    driver = init_driver()

    progress = tqdm(desc="Daily crawling", unit="page")

    try:

        for page in range(1, MAX_PAGE_DAILY + 1):

            new_count = crawl_page_daily(driver, page, existing_ids)

            progress.update(1)

            time.sleep(2)

            if page > 3 and new_count == 0:
                break

    finally:

        driver.quit()
        progress.close()


if __name__ == "__main__":
    main()