import os
import traceback
import time
import PyPDF2
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from login_info import NS_profile

profile = NS_profile()

EMAIL = profile.email
PASSWORD = profile.password

DECLARATIONS_DIR = os.getcwd() + '/declarations/'
CHROME_DRIVER_PATH =  '/home/conor/Downloads/chromedriver-linux64/chromedriver'

WAIT_FOR_DOWNLOAD = 5
WAIT_BETWEEN_CLICKS = 2
ELEMENT_TIMEOUT = 5


def load_browser():
    try:
        # Path to driver
        chrome_service = Service(CHROME_DRIVER_PATH)
        # Create ChromOptions object 
        options = webdriver.ChromeOptions()
        # Set download folder
        prefs = {"download.default_directory": DECLARATIONS_DIR}
        options.add_experimental_option('prefs', prefs)
        # Hide that chrome is being automated
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # Automatically accept unhandled prompts
        options.set_capability('unhandledPromptBehavior', 'accept')
        # Disables some Chrome features to make browser appear less like a bot
        options.add_argument('--disable-blink-features=AutomationControlled')
        # sets the User-Agent for the web requests made by this browser instance. It's used to identify the browser to the web server.
        options.add_argument(f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36')
        # Initialises browser with specified options
        browser = webdriver.Chrome(service=chrome_service, options=options)
        # Delete cookies and reload
        browser.delete_all_cookies()
        browser.execute_script("location.reload(true);")
    except:
        traceback.print_exc()
        print('Failed to load chromedriver. Exiting.')
        exit()
    return browser

def click(browser, element):
    browser.execute_script("arguments[0].click();", element)

def log_in(browser):
    browser.get('https://login.ns.nl/login')
    email = browser.find_element(By.ID, "email")
    email.send_keys(EMAIL)
    password = browser.find_element(By.ID, "password")
    password.send_keys(PASSWORD)
    cookies_refuse = browser.find_element("xpath", '//button[@class="cookie-notice__btn-reject hide-in-settings"]')
    cookies_refuse.click()
    time.sleep(WAIT_BETWEEN_CLICKS)
    button = browser.find_element("xpath", '//input[@value="Inloggen"]')
    button.click()
    betaal_div = WebDriverWait(browser, ELEMENT_TIMEOUT).until(
        expected_conditions.visibility_of_element_located((By.XPATH, '//a[@class="ng-tns-c94-2 mijnNSsubmenu__link icon--invoices" and @href="#/betaaloverzicht"]'))
    )
    click(browser, betaal_div)
    time.sleep(WAIT_BETWEEN_CLICKS)


# Downloads Overzicht for desired_month . If None is supplied, returns first result
# desired_month takes form "Oktober 2023" (in Dutch) 
def download_overview(browser, desired_month=None):
    invoice_rows = WebDriverWait(browser, 30).until(
        expected_conditions.visibility_of_all_elements_located((By.XPATH, '//div[@class="invoicesRow nes-mt-3 nes-mb-3"]'))
    )

    print(f"Found {len(invoice_rows)} invoice rows.")

    # Iterate through the invoice rows to find the specific button and date
    for row in invoice_rows:
        # Find the date within this row
        date_element = row.find_element(By.XPATH, './/nes-text[@class="invoicesRow__column invoicesRow__column--date"]')
        date_text = date_element.text

        # Find the button within this row
        button_element = row.find_element(By.XPATH, './/nes-button[@class="nes-widthAuto"]')

        # If no desired month is supplied, return first result
        if desired_month is None:
            click(browser, button_element)
            time.sleep(WAIT_BETWEEN_CLICKS)
            return date_text

        # Break and return once desired month is reached
        elif date_text == desired_month:
            click(browser, button_element)
            time.sleep(WAIT_BETWEEN_CLICKS)
            return date_text
    
    # TODO: raise exception when desired month cannot be found
    print("No matching month found")
    return 0


def rename_declaration_file(month_of_factuur):
    file_to_rename = DECLARATIONS_DIR + [f for f in os.listdir(DECLARATIONS_DIR) if f.startswith("factuur")][0]
    month, year = month_of_factuur.split(" ")
    new_name = f"{DECLARATIONS_DIR}{year}_{month.lower()}_overzicht.pdf"
    os.rename(file_to_rename, new_name)
    return new_name


def download_main(desired_month=None):
    if not os.path.isdir(DECLARATIONS_DIR):
        print(f'Output directory "{DECLARATIONS_DIR}" doesn\'t exist, please create the directory.')
        exit()

    browser = load_browser()

    print("Attempting to log in...")
    log_in(browser)
    print("Success! Logged in")

    print("Attempting to download pdf...")
    date_downloaded = download_overview(browser, desired_month)
    print(f"Download complete for {date_downloaded}")
    time.sleep(5)

    new_file_path = rename_declaration_file(date_downloaded)
    print("file renamed")
    return new_file_path


if __name__ == "__main__":
    download_main()