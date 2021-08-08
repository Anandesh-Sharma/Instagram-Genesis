# %%
from seleniumwire import webdriver
import time
from config import PROXY
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from helper import get_db
from pymongo import InsertOne
from datetime import datetime

db = get_db()


def extract(keyword, message):
    # %%
    sw_options = {
        'proxy': PROXY
    }
    options = Options()
    # options.add_argument('--headless')
    browser = webdriver.Chrome(options=options)
    browser.get('https://youtube.com')
    # %% search
    search = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="search"]')))
    search.send_keys(keyword)
    s_button = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search-icon-legacy"]')))
    s_button.click()

    scroll_pause_time = 1  # You can set your own pause time. My laptop is a bit slow so I use 1 sec
    screen_height = browser.execute_script("return window.screen.height;")  # get the screen height of the web
    print(screen_height)
    i = 1

    while True:
        # scroll one screen height each time
        browser.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
        i += 1
        time.sleep(scroll_pause_time)
        # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
        scroll_height = browser.execute_script("return document.body.scrollHeight;")
        # Break the loop when the height we need to scroll to is larger than the total scroll height
        # if (screen_height * i) > scroll_height:
        #     break
        try:
            browser.find_element_by_xpath('//ytd-message-renderer')
            break
        except:
            pass

    # %% extract channels
    print('Channel Extraction Started')
    fetched_channels = []
    current_channel_ids = []
    channels = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//ytd-video-renderer')))
    for channel in channels:
        channel_element = channel.find_element_by_xpath('.//ytd-channel-name/div/div/yt-formatted-string/a')
        id = channel_element.get_attribute('href').split('/')[-1]
        name = channel_element.get_attribute('innerHTML').rstrip().lstrip()
        if not db['youtube'].find_one({'_id': id}) and id not in current_channel_ids:
            current_channel_ids.append(id)
            fetched_channels.append(InsertOne({
                '_id': id,
                'keyword': keyword,
                'channel_name': name,
                'message': message,
                'created_at': datetime.utcnow()
            }))
    browser.quit()
    results = db['youtube'].bulk_write(fetched_channels)
    print(results.bulk_api_result)
    return {'status': True, 'message': f"Channels related to {keyword} are extracted successfully"}


