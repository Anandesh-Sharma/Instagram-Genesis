import random
import time
from helper import get_db, MessageClient, fetch_public_data
import os
import csv
import instagram_private_api
from config import proxy, API_PROXY
import pickle
from seleniumwire.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor

FIELDS = ['UserName', 'Email', 'FullName']


def extract_username(link):
    if link[-1] == '/':
        link = link[:-1]
    username = link.split('/')[-1]
    if '?' in username:
        username = username.split('?')[0]

    return username


def get_driver(account):
    WIDTH = 375
    HEIGHT = 667
    PIXEL_RATIO = 2.0
    UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    mobileEmulation = {"deviceMetrics": {"width": WIDTH, "height": HEIGHT, "pixelRatio": PIXEL_RATIO}, "userAgent": UA}
    sw_options = {
        'proxy': proxy('India')
    }
    options = ChromeOptions()
    options.add_argument('--incognito')
    options.binary_location = '/usr/bin/brave-browser'
    # options.add_argument('--user-data-dir=/temp/profile1')
    options.add_experimental_option("mobileEmulation", mobileEmulation)
    driver = Chrome(seleniumwire_options=sw_options, options=options)
    driver.get('https://instagram.com')

    # %%
    cookies = pickle.loads(account['cache_settings']['cookie'])
    ds_user_id = cookies['.instagram.com']['/']['ds_user_id'].value
    sessionid = cookies['.instagram.com']['/']['sessionid'].value

    for i in [{'domain': '.instagram.com',
               'expiry': 1688938731,
               'httpOnly': False,
               'name': 'ds_user_id',
               'path': '/',
               'secure': True,
               'value': f'{ds_user_id}'},

              {'domain': '.instagram.com',
               'expiry': 1688938731,
               'httpOnly': False,
               'name': 'sessionid',
               'path': '/',
               'secure': True,
               'value': f'{sessionid}'}]:
        driver.add_cookie(i)

    # %%
    time.sleep(15)
    driver.refresh()

    return driver


def initiate_insta_user_on_browser(driver, target_username, message):
    # %% Go on the user's page (starts the loop)
    driver.get(f'https://instagram.com/{target_username}')
    # %% Follow the user
    follow = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Follow')]")))
    time.sleep(random.random() + 1)
    follow.click()
    time.sleep(random.random() + 2)
    # %% Click on message button, !!Caution sometimes not available
    message_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button/div[contains(text(), 'Message')]")))
    time.sleep(random.random() + 1)
    message_btn.click()
    time.sleep(random.random() + 2)

    # %% send_message
    text_area = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder]")))
    time.sleep(random.random() + 1)
    text_area.send_keys(message)
    time.sleep(random.random() + 2)

    # %% click send button
    send_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Send')]")))
    send_btn.click()
    time.sleep(random.random())


def save_emails_to_excel(username, email, full_name):
    if not os.path.exists('emails.csv'):
        with open('emails.csv', 'w', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
            writer.writeheader()
            row = {
                'UserName': username,
                'Email': email,
                'FullName': full_name
            }
            writer.writerow(row)
    else:
        with open('emails.csv', 'a', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
            row = {
                'UserName': username,
                'Email': email,
                'FullName': full_name
            }
            writer.writerow(row)


def send_dm(driver, username, message):
    print('Fetching public data for : {}'.format(username))
    public_data = fetch_public_data(10, username)
    if public_data['status']:
        if not public_data['data']:
            return {'status': False, 'message': f'Username : {username} has no data', 'status_code': 1}
        if 'restricted' in public_data:
            return {'status': False, 'message': f'Username : {username} is restricted', 'status_code': 1}
        if 'graphql' in public_data['data']:
            user_id = public_data['data']['graphql']['user']['id']
            print(f"Business Email : {public_data['data']['graphql']['user']['business_email']}")
            if public_data['data']['graphql']['user']['business_email']:
                save_emails_to_excel(
                    username,
                    public_data['data']['graphql']['user']['business_email'],
                    public_data['data']['graphql']['user']['full_name']
                )
    else:
        return {'status': False, 'message': 'Failed to extract the public data', 'status_code': 0}
    initiate_insta_user_on_browser(driver, username, message)
    return {'status': True, 'message': 'Sent message successfully', 'status_code': 4}


while True:
    db = get_db()
    yt_insta_dm = [i for i in
                   db['youtube'].find({'$and': [{'insta_dm_failed': {'$exists': False}}, {'insta_dm': False}]})]
    account = db['accounts'].find_one({'$and': [{'is_blocked': False}, {'message_limit': {'$lt': 30}}]})
    print(account)
    message_limit = account['message_limit']
    driver = get_driver(account)

    for i in yt_insta_dm:
        channel_id = i['_id']
        message = i['message']
        insta_username = extract_username(i['social_handles']['instagram'])

        result = send_dm(driver, insta_username, message)
        print(result)
        if result['status']:
            db['accounts'].update_one({'_id': account['_id']}, {'$inc': {'message_limit': 1}})
            db['youtube'].update_one({'_id': channel_id}, {'$set': {'insta_dm': True}})
            message_limit += 1
            if message_limit >= 30:
                driver.close()
                print('Fetching next account')
                account = db['accounts'].find_one({'$and': [{'is_blocked': False}, {'message_limit': {'$lt': 30}}]})
                driver = get_driver(account)
                if not account:
                    print('Accounts finished')
                    break
                message_limit = account['message_limit']
        elif result['status_code'] == 2:
            driver.close()
            print('Fetching next account')
            account = db['accounts'].find_one({'$and': [{'is_blocked': False}, {'message_limit': {'$lt': 30}}]})
            driver = get_driver(account)
            if not account:
                print('Accounts finished')
                break
            message_limit = account['message_limit']
        elif result['status_code'] == 1:
            db['youtube'].update_one({'_id': channel_id}, {'$set': {'insta_dm_failed': True}}, upsert=True)

        print('Sleeping randomly')
        time.sleep(random.randint(15, 40))

    print("Sleeping for 10 seconds")
    time.sleep(10)
