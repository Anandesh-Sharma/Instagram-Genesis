import time
from urllib.error import URLError
import re
import deathbycaptcha
import instagram_private_api.errors
from instagram_private_api.client import Client
from pymongo import MongoClient
from fake_useragent import UserAgent
from config import *
import sys
import codecs
import datetime
import requests
from pytz import timezone
import json
import secrets
import pickle
from threading import Thread
import random
from seleniumwire import webdriver
from selenium_stealth import stealth
from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from twocaptcha import TwoCaptcha

# useragents
ua = UserAgent()
usable_sessions = []


def death_by_captca(site_key, site_url):
    # Put your DBC account username and password here.
    username = "ishanjindal95"
    password = "Password123456"
    # you can use authtoken instead of user/password combination
    # activate and get the authtoken from DBC users panel

    # Put the proxy and reCaptcha token data
    # recaptchaV3 requires action that is the action that triggers
    # recaptchaV3 validation
    # if not action is provided we use the default value "verify"
    # also you need to provide a minimum score, a number from 0.1 to 0.9,
    # this is the minimum score acceptable from recaptchaV3

    Captcha_dict = {
        'googlekey': site_key,
        'pageurl': site_url}

    # Create a json string
    json_Captcha = json.dumps(Captcha_dict)

    # to use socket client
    # client = deathbycaptcha.SocketClient(username, password, authtoken)
    # to use http client
    client = deathbycaptcha.HttpClient(username, password)

    try:
        balance = client.get_balance()
        print(balance)

        # Put your CAPTCHA type and Json payload here:
        captcha = client.decode(type=4, token_params=json_Captcha)
        if captcha:
            # The CAPTCHA was solved; captcha["captcha"] item holds its
            # numeric ID, and captcha["text"] item its list of "coordinates".
            print("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))
            return captcha['text']
    except deathbycaptcha.AccessDeniedException:
        # Access to DBC API denied, check your credentials and/or balance
        print("error: Access to DBC API denied," +
              "check your credentials and/or balance")


def get_token(sitekey, url):
    solver = TwoCaptcha(apiKey='d70728d18265afda5991a56598140958')

    while True:
        try:
            TOKEN = solver.recaptcha(sitekey=sitekey, url=url)['code']
            break
        except Exception as e:
            print(f'Failed to acquire token, Retrying !! {e}')
            pass

    return TOKEN


def get_browser():
    sw_options = {
        'proxy': proxy(country='India')
    }
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # options.add_argument('--headless')
    # options.binary_location = '/usr/bin/brave-browser'
    # options.add_argument('--incognito')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # options.add_argument('--user-data-dir=/tmp/profile42')
    # options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
    driver = webdriver.Chrome(seleniumwire_options=sw_options, options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc. (NVIDIA Corporation)",
            platform="Linux x86_64",
            webgl_vendor="WebKit",
            renderer=f"Google Inc. (NVIDIA Corporation)~ANGLE (NVIDIA Corporation, GeForce GTX {random.randint(500, 1700)}/PCIe/SSE2, OpenGL 4.5.0 NVIDIA {random.choice([470, 460, 450, 440, 430, 420, 410, 400, 390])}.91.03)",
            fix_hairline=True
            )
    return driver


def send_data_to_wobb(url, data):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = json.dumps(data, indent=1, sort_keys=True, default=str)
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except Exception as e:
        print(f'Request failed to endpoint : {str(e)}')
        return
    print(response.text)


def store_gmail_accounts(email, password):
    driver = get_browser()
    driver.get(
        'https://accounts.google.com/signin/v2/identifier?service=youtube&uilel=3&passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26app%3Ddesktop%26hl%3Den%26next%3Dhttps%253A%252F%252Fwww.youtube.com%252F&hl=en&ec=65620&flowName=GlifWebSignIn&flowEntry=ServiceLogin')

    input_email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@type="email"]')))
    input_email.send_keys(email)

    next_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button/span[contains(text(), 'Next')]")))
    next_button.click()

    time.sleep(random.randint(8, 16))

    input_pass = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))
    input_pass.send_keys(password)

    next_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button/span[contains(text(), 'Next')]")))
    next_button.click()
    time.sleep(random.randint(8, 16))

    driver.get('https://youtube.com')
    x = driver.get_cookies()

    db = get_db()
    db.gmail_accounts.insert_one(
        {
            '_id': email,
            'password': password,
            'cookies': x,
            'limit': 0
        }
    )
    return {'status': True, 'message': f'Account : {email} has been successfully stored'}


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def generate_random_hash():
    return secrets.token_hex(nbytes=16)


def get_ist_timestamp(unix_time=None):
    ist = timezone('Asia/Kolkata')
    if unix_time:
        return datetime.datetime.utcfromtimestamp(unix_time)
    return datetime.datetime.now(ist)


def get_db():
    try:
        client = MongoClient(DB_URI)['Instagram']
    except Exception as e:
        print(str(e) + 'Error In getting database')
        sys.exit(1)
    return client


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def fetch_public_data(max_retries, username):
    global usable_sessions
    db = get_db()
    url = f'https://www.instagram.com/{username}/?__a=1'
    pproxy_retries = int(max_retries * 0.3)
    # get a random user from the database
    res_account = db['accounts'].aggregate([{'$match': {'is_blocked': False}}, {'$sample': {'size': 1}}])
    if res_account:
        for i in res_account:
            cookies = pickle.loads(i['cache_settings']['cookie'])
            try:
                mid = cookies['.instagram.com']['/']['mid'].value
                rur = cookies['.instagram.com']['/']['rur'].value
                ds_user_id = cookies['.instagram.com']['/']['ds_user_id'].value
                sessionid = cookies['.instagram.com']['/']['sessionid'].value
                csrftoken = cookies['.instagram.com']['/']['csrftoken'].value
            except KeyError as e:
                print(f"Cookies error : {str(e)}")
                exit(0)
    else:
        print('No active accounts are there! ->> EXITING')
        exit(0)

    while max_retries != 0:
        session_id = ''.join(
            random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for _ in range(14))
        headers = {
            "Host": "www.instagram.com",
            "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            "sec-ch-ua-mobile": "?1",
            "save-data": "on",
            "upgrade-insecure-requests": "1",
            "user-agent": f"Mozilla/5.0 (Linux; Android {random.randrange(6, 11)}; Redmi Note {random.randrange(5, 11)} Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "document",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en-GB;q=0.9,en-IN;q=0.8,en;q=0.7",
            "cookie": f'mid={mid}; ds_user_id={ds_user_id}; rur={rur}; sessionid={ds_user_id}%3A{session_id}%3A{random.randrange(0, 30)};'
        }
        try:
            if True:
                # print('hello')
                if len(usable_sessions) > 2:
                    print('Using existing active session')
                    random_session = random.choice(usable_sessions)
                    try:
                        with random_session.get(url) as response:
                            data = response.json()
                    except:
                        usable_sessions.remove(random_session)
                        continue
                else:
                    with requests.Session() as session:
                        print('Creating new session')
                        session.headers.update(headers)

                        if max_retries <= pproxy_retries:
                            session.proxies.update(proxy())
                        else:
                            session.proxies.update(PROXY)
                        data = session.get(url).json()
                        if 'graphql' in data:
                            usable_sessions.append(session)
                    # print(data)
            # else:
            #     data = requests.get(url=url, headers=headers, proxies=PROXY).json()
            if 'graphql' in data:
                print({'status': True, 'message': f'Successfully Extracted data for username : {username}!',
                       'module': 'helper.fetch_public_data', 'full': True})

                return {'status': True, 'message': f'Successfully Extracted data for username : {username}!',
                        'module': 'helper.fetch_public_data', 'data': data, 'full': True}

            elif data == {}:
                # print({'status': True, 'message': f'No data for username : {username}',
                #        'module': 'helper.fetch_public_data'})
                return {'status': True, 'message': f'No data for username : {username}', 'data': data,
                        'module': 'helper.fetch_public_data'}
            elif 'graphql' not in data:

                print({'status': True, 'message': f'Account restricted username : {username}',
                       'module': 'helper.fetch_public_data'})
                return {'status': True, 'data': data, 'restricted': True,
                        'message': f'Account restricted username : {username}', 'module': 'helper.fetch_public_data'}

            else:
                print({'status': False, 'message': f'Unknown data for username : {username}',
                       'module': 'helper.fetch_public_data'})
                max_retries -= 1
        except Exception as e:
            # import traceback
            # print(traceback.print_exc())
            # print(e)
            max_retries -= 1
    if max_retries == 0:
        # print({'status': False, 'message': f"Max tries exceeded! for {username}"})
        return {'status': False, 'message': f"Max tries exceeded! for {username}"}


def clear_the_text(element):
    element.send_keys(Keys.CONTROL + 'a')
    element.send_keys(Keys.DELETE)


def natural_type(element, text):
    for i in text:
        element.send_keys(i)
        time.sleep(random.random())


def update_profile(api, old_username, sessionid, ds_user_id):
    browser = get_browser()
    browser.get('https://instagram.com')
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
        try:
            browser.add_cookie(i)
        except:
            return {'status': False, 'message': f'Issue with cookies in : {old_username}'}

    browser.refresh()
    browser.get(f'https://instagram.com/{old_username}')
    # upload profile picture
    try:
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, '//button[@title="Change Profile Photo"]'))).click()
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div/div/div[2]/form/input'))).send_keys(
            '/home/hash/Instagram-Genesis/download.jpeg')
    except:
        try:
            WebDriverWait(browser, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//input[@accept="image/jpeg,image/png"]'))).send_keys(
                '/home/hash/Instagram-Genesis/download.jpeg')
        except:
            browser.close()
            return {'status': False, 'message': 'Failed to update profile picture'}

    # edit profile info
    browser.get('https://www.instagram.com/accounts/edit/')
    username = f'wobb_{random.randint(500, 10000)}'
    while not api.check_username(username)['available']:
        username = f'wobb_{random.randint(500, 10000)}'
    print(username)
    try:
        name = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pepName"]')))
        clear_the_text(name)
        natural_type(name, PROFILE['name'])

        add_username = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pepUsername"]')))
        clear_the_text(add_username)
        natural_type(add_username, username)

        website = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pepWebsite"]')))
        clear_the_text(website)
        natural_type(website, PROFILE['website'])

        bio = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pepBio"]')))
        clear_the_text(bio)
        natural_type(bio, PROFILE['bio'])

        email = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pepEmail"]')))
        clear_the_text(email)
        natural_type(email, f'{username}@gmail.com')

        phone = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pepPhone Number"]')))
        clear_the_text(phone)

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Submit')]"))).click()
    except:
        browser.close()
        return {'status': False, 'message': 'Failed to update profile info'}
    time.sleep(15)
    browser.close()

    # verify the update
    profile_updated = False
    verify_username = api.check_username(username)
    if not verify_username['available']:
        profile_updated = True

    # update in db as well
    db = get_db()
    if profile_updated:
        db['accounts'].update_one({'username': old_username}, {'$set': {'username': username, 'updated_profile': True}})
    else:
        db['accounts'].update_one({'username': old_username}, {'$unset': {'updated_profile': 1}})
        return {'status': False, 'message': 'Profile didnt updated', 'username': old_username}

    return {'status': True, 'message': 'Successfully updated profile', 'username': username}


def store_account(username: str, password: str) -> dict:
    """
    :param password:
    :param username:
    :return: dict of results
    """
    db = get_db()
    found = True if db['accounts'].find_one({'_id': username}) else False
    if found:
        return {'status': True, 'message': f'Account already exists: {username}', 'module': 'helper.store_account'}

    while 1:
        try:
            api = Client(username=username, password=password, proxy=API_PROXY,
                         timeout=60)
            break
        except TimeoutError:
            pass
        except instagram_private_api.errors.ClientConnectionError:
            pass
        except URLError:
            pass
        except json.decoder.JSONDecodeError:
            pass
        except instagram_private_api.errors.ClientLoginError:
            return {'status': True, 'message': f'Wrong Password:  {username}',
                    'module': 'helper.store_account'}
        except instagram_private_api.errors.ClientChallengeRequiredError:
            return {'status': True, 'message': f'Is Blocked:  {username}',
                    'module': 'helper.store_account'}
        except Exception as e:
            return {'status': False, 'message': f'Exception occurred :  {username} : {str(e)}',
                    'module': 'helper.store_account'}

    # update profile
    result = update_profile(api=api, ds_user_id=api.get_cookie_value('ds_user_id'),
                            sessionid=api.get_cookie_value('sessionid'), username=username)
    print(result)
    # check if the username already exists
    if not found:
        cache_settings = api.settings
        db['accounts'].insert_one({
            '_id': api.username,
            'password': api.password,
            'cache_settings': cache_settings,
            'is_occupied': False,
            'fetched': 0,
            'is_blocked': False,
            'cookie_expiry': datetime.datetime.utcfromtimestamp(api.cookie_jar.auth_expires),
            'created_at': datetime.datetime.utcnow()
        })
        return {'status': True, 'message': f'Successfully added account: {api.username}',
                'module': 'helper.store_account'}


def target_all_work(username):
    result_follower = add_follower_work(username)
    result_following = add_following_work(username)

    if result_follower['status'] and result_following['status']:
        return {'status': True, 'message': f'Successfully added : {username}'}


def add_follower_work(username):
    db = get_db()
    max_retries = 20
    # first fetch the public data to get the user_id
    result = fetch_public_data(max_retries, username)

    if result['status']:

        # check if data is null
        if result['data'] == {}:
            return result

        if 'restricted' in result:
            return result
        data = result['data']
        user_id = int(data['graphql']['user']['id'])
        # check if this user_id already present ?
        db_result = db['target_usernames'].find_one({'_id': user_id})
        if db_result:
            # check the update duration i.e. 1 month
            delta = datetime.datetime.utcnow() - db_result['updated_at']
            if delta.days >= 30:
                db['target_usernames'].update_one({'_id': user_id},
                                                  {'$set': {
                                                      'graphql': data,
                                                      'username': username,
                                                      'updated_at': datetime.datetime.utcnow()
                                                  }})
            if 'follower' not in db_result and 'graphql' in db_result:
                db['target_usernames'].update_one({'_id': user_id},
                                                  {'$set': {'follower': True,
                                                            'updated_at': datetime.datetime.utcnow()}},
                                                  upsert=True)
            return {'status': True, 'message': f'User already exists: {username}'}

        else:
            data['_id'] = user_id
            data['username'] = username
            data['follower'] = True
            data['created_at'] = datetime.datetime.utcnow()
            data['updated_at'] = datetime.datetime.utcnow()
            db['target_usernames'].insert_one(data)
            return {'status': True, 'message': f'Successfully added {username}'}
    else:
        return {'status': False, 'message': f'Failed to add the username ERROR: {result["message"]}'}


def add_following_work(username):
    db = get_db()
    max_retries = 20
    # if target_username already exists:
    # first fetch the public data to get the user_id
    result = fetch_public_data(max_retries, username)

    if result['status']:
        # check if data is null
        if result['data'] == {}:
            return result
        if 'restricted' in result:
            return result
        data = result['data']
        user_id = int(data['graphql']['user']['id'])

        # check if this user_id already present ?
        db_result = db['target_usernames'].find_one({'_id': user_id})
        if db_result:
            # check the update duration i.e. 1 month
            delta = datetime.datetime.utcnow() - db_result['updated_at']
            if delta.days >= 30:
                db['target_usernames'].update_one({'_id': user_id},
                                                  {'$set': {
                                                      'graphql': data,
                                                      'username': username,
                                                      'updated_at': datetime.datetime.utcnow()
                                                  }})
            if 'following' not in db_result and 'graphql' in db_result:
                db['target_usernames'].update_one({'_id': user_id},
                                                  {'$set': {'following': True,
                                                            'updated_at': datetime.datetime.utcnow()}},
                                                  upsert=True)
            return {'status': True, 'message': f'User already exists: {username}'}

        else:
            data['_id'] = int(data['graphql']['user']['id'])
            data['username'] = username
            data['following'] = True
            data['created_at'] = datetime.datetime.utcnow()
            data['updated_at'] = datetime.datetime.utcnow()
            db['target_usernames'].insert_one(data)
            return {'status': True, 'message': f'Successfully added {username}'}
    else:
        return {'status': False, 'message': f'Failed to add the username ERROR: {result["message"]}'}


def only_public_data(username, wobb_ep):
    max_retries = 15
    db = get_db()
    # check if already exists
    db_result = db['target_usernames'].find_one({'username': username})
    if db_result:
        if wobb_ep:
            send_data_to_wobb(wobb_ep, db_result)
        return {'status': True, 'message': f'User already exists: {username}'}

    result = fetch_public_data(max_retries, username)
    # if data received successfully
    if result['status']:
        data = result['data']
        data['username'] = username
        if 'full' in result:
            data['_id'] = int(data['graphql']['user']['id'])
            if db['target_usernames'].find_one({'_id': data['_id']}):
                return {'status': True, 'message': f'User already exists: {username}'}
        elif 'restricted' in result:
            data['restricted'] = True
        else:
            pass

        data['created_at'] = datetime.datetime.utcnow()
        data['updated_at'] = datetime.datetime.utcnow()
        db['target_usernames'].insert_one(data)
        if wobb_ep:
            send_data_to_wobb(wobb_ep, data)
        return {'status': True, 'message': f'Successfully extracted public data for : {username}'}
    else:
        return {'status': False, 'message': result['message']}


class MessageClient(Client):
    def extract_urls(self, text):
        url_regex = (
            r"((?:(?:http|https|Http|Https|rtsp|Rtsp)://"
            r"(?:(?:[a-zA-Z0-9$\-\_\.\+\!\*\'\(\)\,\;\?\&\=]|(?:%[a-fA-F0-9]"
            r"{2})){1,64}(?::(?:[a-zA-Z0-9$\-\_\.\+\!\*\'\(\)\,\;\?\&\=]|"
            r"(?:%[a-fA-F0-9]{2})){1,25})?@)?)?(?:(?:(?:[a-zA-Z0-9"
            r"\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF\_][a-zA-Z0-9"
            r"\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF\_\-]{0,64}\.)+(?:(?:aero|"
            r"arpa|asia|a[cdefgilmnoqrstuwxz])|(?:biz|b[abdefghijmnorstvwyz])|"
            r"(?:cat|com|coop|c[acdfghiklmnoruvxyz])|d[ejkmoz]|(?:edu|e[cegrstu])"
            r"|f[ijkmor]|(?:gov|g[abdefghilmnpqrstuwy])|h[kmnrtu]|(?:info|int|i"
            r"[delmnoqrst])|(?:jobs|j[emop])|k[eghimnprwyz]|l[abcikrstuvy]|(?:mil"
            r"|mobi|museum|m[acdeghklmnopqrstuvwxyz])|(?:name|net|n[acefgilopruz])"
            r"|(?:org|om)|(?:pro|p[aefghklmnrstwy])|qa|r[eosuw]|s[abcdeghijklmnort"
            r"uvyz]|(?:tel|travel|t[cdfghjklmnoprtvwz])|u[agksyz]|v[aceginu]"
            r"|w[fs]|(?:\u03B4\u03BF\u03BA\u03B9\u03BC\u03AE|"
            r"\u0438\u0441\u043F\u044B\u0442\u0430\u043D\u0438\u0435|\u0440\u0444|"
            r"\u0441\u0440\u0431|\u05D8\u05E2\u05E1\u05D8|"
            r"\u0622\u0632\u0645\u0627\u06CC\u0634\u06CC|"
            r"\u0625\u062E\u062A\u0628\u0627\u0631|\u0627\u0644\u0627\u0631\u062F"
            r"\u0646|\u0627\u0644\u062C\u0632\u0627\u0626\u0631|"
            r"\u0627\u0644\u0633\u0639\u0648\u062F\u064A\u0629|"
            r"\u0627\u0644\u0645\u063A\u0631\u0628|\u0627\u0645\u0627\u0631\u0627"
            r"\u062A|\u0628\u06BE\u0627\u0631\u062A|\u062A\u0648\u0646\u0633|"
            r"\u0633\u0648\u0631\u064A\u0629|\u0641\u0644\u0633\u0637\u064A\u0646|"
            r"\u0642\u0637\u0631|\u0645\u0635\u0631|"
            r"\u092A\u0930\u0940\u0915\u094D\u0937\u093E|\u092D\u093E\u0930\u0924|"
            r"\u09AD\u09BE\u09B0\u09A4|\u0A2D\u0A3E\u0A30\u0A24|"
            r"\u0AAD\u0ABE\u0AB0\u0AA4|\u0B87\u0BA8\u0BCD\u0BA4\u0BBF\u0BAF\u0BBE|"
            r"\u0B87\u0BB2\u0B99\u0BCD\u0B95\u0BC8|"
            r"\u0B9A\u0BBF\u0B99\u0BCD\u0B95\u0BAA\u0BCD\u0BAA\u0BC2\u0BB0\u0BCD|"
            r"\u0BAA\u0BB0\u0BBF\u0B9F\u0BCD\u0B9A\u0BC8|\u0C2D\u0C3E\u0C30\u0C24"
            r"\u0C4D|\u0DBD\u0D82\u0D9A\u0DCF|\u0E44\u0E17\u0E22|\u30C6\u30B9"
            r"\u30C8|\u4E2D\u56FD|\u4E2D\u570B|\u53F0\u6E7E|\u53F0\u7063|\u65B0"
            r"\u52A0\u5761|\u6D4B\u8BD5|\u6E2C\u8A66|\u9999\u6E2F|\uD14C\uC2A4"
            r"\uD2B8|\uD55C\uAD6D|xn--0zwm56d|xn--11b5bs3a9aj6g|xn--3e0b707e"
            r"|xn--45brj9c|xn--80akhbyknj4f|xn--90a3ac|xn--9t4b11yi5a|xn--clchc0ea"
            r"0b2g2a9gcd|xn--deba0ad|xn--fiqs8s|xn--fiqz9s|xn--fpcrj9c3d|xn--"
            r"fzc2c9e2c|xn--g6w251d|xn--gecrj9c|xn--h2brj9c|xn--hgbk6aj7f53bba|xn"
            r"--hlcj6aya9esc7a|xn--j6w193g|xn--jxalpdlp|xn--kgbechtv|xn--kprw13d|"
            r"xn--kpry57d|xn--lgbbat1ad8j|xn--mgbaam7a8h|xn--mgbayh7gpa|"
            r"xn--mgbbh1a71e|xn--mgbc0a9azcg|xn--mgberp4a5d4ar|xn--o3cw4h|"
            r"xn--ogbpf8fl|xn--p1ai|xn--pgbs0dh|xn--s9brj9c|xn--wgbh1c|xn--wgbl6a|"
            r"xn--xkc2al3hye2a|xn--xkc2dl3a5ee0h|xn--yfro4i67o|xn--ygbi2ammx|"
            r"xn--zckzah|xxx)|y[et]|z[amw]))|(?:(?:25[0-5]|2[0-4][0-9]|"
            r"[0-1][0-9]{2}|[1-9][0-9]|[1-9])\.(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]"
            r"{2}|[1-9][0-9]|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[1-9]"
            r"[0-9]|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[1-9][0-9]|"
            r"[0-9])))(?::\d{1,5})?(?:/(?:(?:[a-zA-Z0-9\u00A0-\uD7FF\uF900-\uFDCF"
            r"\uFDF0-\uFFEF\;\/\?\:\@\&\=\#\~\-\.\+\!\*\'\(\)\,\_])|"
            r"(?:%[a-fA-F0-9]{2}))*)?)(?:\b|$)"
        )  # noqa
        urls = re.findall(url_regex, text)

        return urls

    def send_message(self, message: str, user_id: int, user_ids: list):
        """
        This function sends messages to the list of user_ids
        :param message:
        :param user_id:
        :return:
        """
        links = self.extract_urls(message)
        data = {"client_context": self.generate_uuid(), "action": "send_item"}
        item_type = 'link' if links else 'text'
        if item_type == 'link':
            data["link_text"] = message
            data["link_urls"] = json.dumps(links)
        if item_type == 'text':
            data["text"] = message

        url = f"direct_v2/threads/broadcast/{item_type}/"

        data["recipient_users"] = f'[{user_ids}]'
        data['_uuid'] = self.uuid
        data['_csrftoken'] = self.csrftoken

        response = self._call_api(url, params=data)
        if response['status_code'] == '200':
            return {'status': True, 'message': f'Send successfully to : {user_id}'}
        else:
            return {'status': False, 'message': f'Failed to send message to : {user_id}'}
