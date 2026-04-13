'''
A robust Selenium-based scraper designed to automate the collection of academic PDFs from
a DSpace repository. The script navigates multiple pages, handles dynamic elements,
and includes error-recovery logic to ensure a continuous download pipeline into a local
raw data directory.
'''

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Config
COLLECTION_URL = "https://repositorio.ufrn.br/collections/a7202bae-5682-427c-b668-7289d877375b?cp.page="
DOWNLOAD_DIR = os.path.abspath(os.path.join("data", "raw"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True 
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = setup_driver()
    doc_counter = 1
    wait = WebDriverWait(driver, 30)

    try:
        for page_num in range(1, 13):
            print(f"\n[+] Navigating to page {page_num}...")
            driver.get(f"{COLLECTION_URL}{page_num}")

            try:
                # Localiza os links dos itens
                items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.item-list-title")))
                item_links = [item.get_attribute("href") for item in items]
                print(f"[*] Found {len(item_links)} items on page {page_num}.")

                for link in item_links:
                    print(f"  [{doc_counter}] Attempting: {link}")
                    driver.get(link)
                    
                    success = False
                    attempts = 0
                    while attempts < 3 and not success:
                        try:
                            # Tenta localizar e clicar no botão de download
                            download_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-primary[href*='/bitstreams/']")))
                            download_btn.click()
                            print(f"  [v] Download triggered.")
                            time.sleep(4)
                            doc_counter += 1
                            success = True
                        except (StaleElementReferenceException, TimeoutException):
                            attempts += 1
                            print(f"  [!] Element stale or timeout. Retry {attempts}/3...")
                            time.sleep(2)
                            driver.refresh() # Atualiza a página no retry para garantir
                    
                    if not success:
                        print(f"  [X] Skipped item after 3 failed attempts.")

            except Exception as e:
                print(f"  [!] Critical error on page {page_num}: {e}")
                driver.save_screenshot(f"error_page_{page_num}.png")

            if doc_counter > 250: break

    finally:
        print(f"\n[!] Process finished. Total attempted: {doc_counter - 1}")
        driver.quit()

if __name__ == "__main__":
    main()
