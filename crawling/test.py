import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

url = "https://batdongsan.com.vn/ban-can-ho-chung-cu-duong-phuoc-thien-phuong-long-binh-3-the-origami-vinhomes-grand-park/gio-hang-noi-bo-vua-bung-2pn-view-vuon-nhat-gia-soc-3-568-ty-nhan-nha-ngay-don-tet-2026-pr45140674"

options = Options()
# options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get(url)

wait = WebDriverWait(driver, 20)

driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")

iframe = wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//iframe[contains(@data-src,'google.com/maps')]")
    )
)

data_src = iframe.get_attribute("data-src")

match = re.search(r"q=([-0-9.]+),([-0-9.]+)", data_src)

if match:
    print("Latitude:", match.group(1))
    print("Longitude:", match.group(2))
else:
    print("Không tìm thấy tọa độ")

driver.quit()
