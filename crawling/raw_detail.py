import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re


def create_driver(headless=False):
    options = uc.ChromeOptions()
    options.headless = headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options)
    return driver


def load_page(driver, url, timeout=20):
    driver.get(url)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )


def scroll_middle(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(1)


def wait_for_map(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[contains(@data-src,'google.com/maps')]")
            )
        )
    except:
        pass


def parse_title(soup):
    tag = soup.find("h1", class_="re__pr-title")
    return tag.get_text(strip=True) if tag else None


def parse_breadcrumb(soup):
    result = {
        "transaction_type": None,
        "city": None,
        "district": None,
        "property_type": None,
        "project_name_breadcrumb": None
    }

    breadcrumb = soup.find("div", class_="re__breadcrumb")
    if not breadcrumb:
        return result

    texts = [a.get_text(strip=True) for a in breadcrumb.find_all("a")]

    if len(texts) > 0:
        result["transaction_type"] = texts[0]
    if len(texts) > 1:
        result["city"] = texts[1]
    if len(texts) > 2:
        result["district"] = texts[2]
    if len(texts) > 3:
        last = texts[3]
        if " tại " in last:
            property_type, project_name = last.split(" tại ", 1)
            result["property_type"] = property_type.strip()
            result["project_name_breadcrumb"] = project_name.strip()
        else:
            result["property_type"] = last

    return result


def parse_price_block(soup):
    result = {
        "price": None,
        "price_per_m2": None,
        "area": None,
        "bedrooms": None
    }

    block = soup.find("div", class_="re__pr-short-info")
    if not block:
        return result

    items = block.find_all("div", class_="re__pr-short-info-item")

    for item in items:
        label = item.find("span", class_="title")
        value = item.find("span", class_="value")
        ext = item.find("span", class_="ext")

        if not label or not value:
            continue

        label_text = label.get_text(strip=True)

        if "Khoảng giá" in label_text:
            result["price"] = value.get_text(strip=True)
            result["price_per_m2"] = ext.get_text(strip=True) if ext else None
        elif "Diện tích" in label_text:
            result["area"] = value.get_text(strip=True)
        elif "Phòng ngủ" in label_text:
            result["bedrooms"] = value.get_text(strip=True)

    return result


def parse_specs(soup):
    result = {
        "bathrooms": None,
        "house_direction": None,
        "balcony_direction": None,
        "legal": None,
        "interior": None
    }

    specs = soup.find_all("div", class_="re__pr-specs-content-item")

    for spec in specs:
        title = spec.find("span", class_="re__pr-specs-content-item-title")
        value = spec.find("span", class_="re__pr-specs-content-item-value")

        if not title or not value:
            continue

        t = title.get_text(strip=True)
        v = value.get_text(strip=True)

        if "Số phòng tắm" in t:
            result["bathrooms"] = v
        elif "Hướng nhà" in t:
            result["house_direction"] = v
        elif "Hướng ban công" in t:
            result["balcony_direction"] = v
        elif "Pháp lý" in t:
            result["legal"] = v
        elif "Nội thất" in t:
            result["interior"] = v

    return result


def parse_project_info(soup):
    result = {
        "project_name": None,
        "project_status": None,
        "developer": None
    }

    name = soup.find("div", class_="re__project-title")
    result["project_name"] = name.get_text(strip=True) if name else None

    status = soup.find("span", class_="re__long-text")
    result["project_status"] = status.get_text(strip=True) if status else None

    developer_block = soup.find("div", class_="re__row-item re__footer-content")
    if developer_block:
        result["developer"] = developer_block.get_text(strip=True)

    return result


def parse_metadata(soup):
    result = {
        "posted_date": None,
        "expired_date": None,
        "listing_type": None,
        "listing_id": None
    }

    items = soup.find_all("div", class_="js__pr-config-item")

    for item in items:
        title = item.find("span", class_="title")
        value = item.find("span", class_="value")

        if not title or not value:
            continue

        t = title.get_text(strip=True)
        v = value.get_text(strip=True)

        if "Ngày đăng" in t:
            result["posted_date"] = v
        elif "Ngày hết hạn" in t:
            result["expired_date"] = v
        elif "Loại tin" in t:
            result["listing_type"] = v
        elif "Mã tin" in t:
            result["listing_id"] = v

    return result


def parse_description(soup):
    block = soup.find("div", class_="re__detail-content")
    if not block:
        return None

    full_text = block.get_text(separator="\n", strip=True)
    if "Thông tin chi tiết" in full_text:
        full_text = full_text.split("Thông tin chi tiết")[0]

    return full_text


def parse_phone(soup):
    phone = soup.find("span", string=lambda x: x and "Hiện số" in x)
    return phone.get_text(strip=True) if phone else None


def parse_coordinates_text(soup):
    tag = soup.find("div", class_="place-name")
    return tag.get_text(strip=True) if tag else None


def parse_map_coordinates(soup):
    result = {"latitude": None, "longitude": None}

    iframe = soup.find("iframe", attrs={"data-src": True})
    if not iframe:
        return result

    data_src = iframe.get("data-src", "")
    match = re.search(r"q=([-0-9.]+),([-0-9.]+)", data_src)

    if match:
        result["latitude"] = float(match.group(1))
        result["longitude"] = float(match.group(2))

    return result


def scrape_listing(url, headless=False):
    driver = create_driver(headless=headless)
    load_page(driver, url)
    scroll_middle(driver)
    wait_for_map(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    data = {
        "url": url,
        "scrape_time": datetime.utcnow().isoformat(),
        "title": parse_title(soup),
        "coordinates_text": parse_coordinates_text(soup),
        "phone_number": parse_phone(soup),
        "description": parse_description(soup),
    }

    data.update(parse_breadcrumb(soup))
    data.update(parse_price_block(soup))
    data.update(parse_specs(soup))
    data.update(parse_project_info(soup))
    data.update(parse_metadata(soup))
    data.update(parse_map_coordinates(soup))

    driver.quit()
    return data


if __name__ == "__main__":
    URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-duong-phuoc-thien-phuong-long-binh-3-the-origami-vinhomes-grand-park/gio-hang-noi-bo-vua-bung-2pn-view-vuon-nhat-gia-soc-3-568-ty-nhan-nha-ngay-don-tet-2026-pr45140674"

    result = scrape_listing(URL, headless=False)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Done.")
