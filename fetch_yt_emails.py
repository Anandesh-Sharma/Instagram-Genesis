import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from helper import get_db, death_by_captca, get_browser

LIMIT = 10
db = get_db()


def fetch_yt_email(channel):

    driver = get_browser()

    if channel[0] == 'U' and len(channel) == 24:
        site_url = f"https://www.youtube.com/channel/{channel}/about"
    else:
        site_url = f"https://www.youtube.com/c/{channel}/about"

    print(site_url)

    # get accounts
    account = db['gmail_accounts'].find_one({'limit': {'$lt': LIMIT}})
    driver.get(site_url)

    driver.delete_all_cookies()

    for i in account['cookies']:
        driver.add_cookie(i)

    driver.refresh()

    site_key = "6Lf39AMTAAAAALPbLZdcrWDa8Ygmgk_fmGmrlRog"

    verify_email = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//tp-yt-paper-button[@aria-label="View email address"]')))
    verify_email.click()
    time.sleep(10)
    token = death_by_captca(site_key, site_url)

    textarea = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//textarea')))
    attrib = textarea.get_attribute('style')
    attrib = attrib.replace('display: none;', '')
    print(attrib)

    driver.execute_script(f"arguments[0].style = '{attrib}';", textarea)

    textarea.send_keys(token)

    submit = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button[@id="submit-btn"]')))
    submit.click()
    time.sleep(10)
    email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@id="email"]'))).text
    print(email)
