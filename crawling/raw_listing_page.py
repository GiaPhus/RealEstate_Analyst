import os
import csv
import time
import logging
from datetime import datetime, timezone

from tqdm import tqdm
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://batdongsan.com.vn/nha-dat-ban-tp-hcm"

DATA_DIR = "data"
CHECKPOINT_DIR = "checkpoint"
LOG_DIR = "log"

CSV_FILE = os.path.join(DATA_DIR, "listing.csv")
CHECKPOINT_FILE = os.path.join(CHECKPOINT_DIR, "listing_checkpoint.txt")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

WAIT_TIMEOUT = 20


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )


def init_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--window-size=1920,1080")

    # (tuỳ chọn) tắt ảnh cho nhẹ
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # ✅ Windows + auto-detect Chrome + auto match driver
    driver = uc.Chrome(options=options)

    driver.set_page_load_timeout(60)
    return driver


def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["listing_id", "url", "crawl_time"])


def append_listing(listing_id, url):
    crawl_time = datetime.now(timezone.utc).isoformat()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([listing_id, url, crawl_time])


def load_existing_ids():
    ids = set()
    if not os.path.exists(CSV_FILE):
        return ids

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("listing_id"):
                ids.add(row["listing_id"])
    return ids


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return 0
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        s = f.read().strip()
        return int(s) if s else 0


def save_checkpoint(page):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        f.write(str(page))


def build_page_url(page):
    return BASE_URL if page == 1 else f"{BASE_URL}/p{page}"


def crawl_page(driver, page, existing_ids):
    url = build_page_url(page)
    logging.info(f"Crawling page {page} | {url}")

    driver.get(url)

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a.js__product-link-for-product-id")
            )
        )
    except Exception:
        logging.info(f"No listings found at page {page}")
        return 0

    elements = driver.find_elements(By.CSS_SELECTOR, "a.js__product-link-for-product-id")

    new_count = 0
    for el in elements:
        listing_id = el.get_attribute("data-product-id")
        href = el.get_attribute("href")

        if not listing_id or not href:
            continue
        if listing_id in existing_ids:
            continue

        append_listing(listing_id, href)
        existing_ids.add(listing_id)
        new_count += 1

    logging.info(f"Page {page} | Found: {len(elements)} | New: {new_count}")
    return new_count


def main():
    ensure_dirs()
    setup_logger()
    init_csv()

    existing_ids = load_existing_ids()
    start_page = load_checkpoint() + 1

    logging.info(f"Starting crawler from page {start_page}")

    driver = init_driver()

    progress = tqdm(desc="Crawling pages", unit="page", dynamic_ncols=True)
    page = start_page

    try:
        while True:
            new_count = crawl_page(driver, page, existing_ids)
            if new_count == 0:
                break

            save_checkpoint(page)
            progress.update(1)
            page += 1
            time.sleep(2)

    finally:
        # ✅ tránh crash vặt lúc quit trên Windows
        try:
            driver.quit()
        except Exception:
            pass
        progress.close()

    logging.info("Crawler finished")


if __name__ == "__main__":
    main()
