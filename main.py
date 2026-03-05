import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
    
base_url = "https://www.cclerk.hctx.net/Applications/WebSearch/FRCL_R.aspx#"

current_dir = os.path.dirname(os.path.abspath(__file__))
save_folder = os.path.join(current_dir, "pdfs")
os.makedirs(save_folder, exist_ok=True)

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(save_folder),
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
})

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

driver.get(base_url)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))

month_dropdown = Select(driver.find_element(By.XPATH, "//select[contains(@id,'Month')]"))
month_dropdown.select_by_visible_text("April")

search_button = driver.find_element(By.XPATH, "//input[@value='SEARCH' or @value='Search']")
search_button.click()

time.sleep(5)  # Wait for the page to load

def wait_for_new_download(old_files, timeout=60):
    """Wait until a new file appears and finishes downloading"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_files = set(glob.glob(os.path.join(save_folder, "*")))
        new_files = current_files - old_files

        if new_files:
            newest = max(new_files, key=os.path.getctime)

            # Wait until Chrome finishes download
            if not newest.endswith(".crdownload"):
                return newest

        time.sleep(0.5)

    raise TimeoutError("Download timed out")

def download_current_page():
    links = driver.find_elements(By.LINK_TEXT, "FRCL")

    if not links:
        links = driver.find_elements(By.PARTIAL_LINK_TEXT, "FRCL")
    
    for link in links:
        try:    
            link_text = link.text.strip().replace("/", "-")

            if (f"{link_text}.pdf" in os.listdir(save_folder)):
                print(f"Already downloaded: {link_text}.pdf")
                continue
            
            # Capture files BEFORE clicking
            before_download = set(glob.glob(os.path.join(save_folder, "*")))

            link.click()

            # Wait for new file
            downloaded_file = wait_for_new_download(before_download)

            new_path = os.path.join(save_folder, f"{link_text}.pdf")

            os.rename(downloaded_file, new_path)

            print(f"Saved as: {new_path}")

        except Exception as e:
            print(f"Error downloading {link_text}: {e}")

for page in range(2,11):
    print(f"Processing page {page}...")
    
    download_current_page()
    try:
        # Wait until the page link is clickable
        page_link = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//a[normalize-space()='{page}']")
            )
        )

        driver.execute_script("arguments[0].scrollIntoView();", page_link)
        driver.execute_script("arguments[0].click();", page_link)

        # Wait for page content to refresh
        wait.until(EC.staleness_of(page_link))

    except Exception as e:
        print(f"Stopped at page {page}: {e}")
        break

driver.quit()
print("Download complete. PDFs saved in the 'pdfs' folder.")