import queue
from urllib.error import URLError
import random
import instagram_private_api.errors
from instagram_private_api.client import Client
from pymongo import MongoClient
from pymongo import errors
from fake_useragent import UserAgent
from config import *
import sys
import codecs
import datetime
import requests
from pytz import timezone
from celery import Celery
import json
import secrets
import pickle
from threading import Thread

# useragents
ua = UserAgent()
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
public_data_celery = Celery('helper', broker='pyamqp://guest@localhost//', backend='redis://localhost:6379/0')
accounts_celery = Celery('accounts', broker='pyamqp://guest@localhost//', backend='redis://localhost:6379/0')


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


class ThreadWithReturnValue(object):
    def __init__(self, target=None, args=(), **kwargs):
        self._que = queue.Queue()
        self._t = Thread(target=lambda q, arg1, kwargs1: q.put(target(*arg1, **kwargs1)),
                         args=(self._que, args, kwargs), )
        self._t.start()

    def join(self):
        self._t.join()
        return self._que.get()


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
    db = get_db()
    url = f'https://www.instagram.com/{username}/?__a=1'
    max_retries = max_retries
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

    # print(f'Started: {username}')
    while max_retries != 0:
        session_id = ''.join(
            random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for _ in range(14))
        headers = {
            'authority': 'www.instagram.com',
            'cache-control': 'max-age=0',
            'sec-ch-ua': f'"Chromium";v=f"9{random.randrange(0, 9)}", " Not A;Brand";v=f"{random.randrange(0, 9)}", "Microsoft Edge";v=f"{random.randrange(0, 9)}"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': ua.random,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'cross-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
            'cookie': f'mid={mid}; csrftoken={csrftoken}; ds_user_id={ds_user_id}; rur={rur};'
        }
        try:

            data = requests.get(url=url, headers=headers, proxies=PROXY).json()
            if 'graphql' in data:
                return {'status': True, 'message': f'Successfully Extracted data for username : {username}!',
                        'module': 'helper.fetch_public_data', 'data': data, 'full': True}
            elif data == {}:
                # print({'status': True, 'message': f'No data for username : {username}',
                #        'module': 'helper.fetch_public_data'})
                return {'status': True, 'message': f'No data for username : {username}', 'data': data,
                        'module': 'helper.fetch_public_data'}
            elif 'graphql' not in data:
                # print({'status': True, 'message': f'Account restricted username : {username}',
                #        'module': 'helper.fetch_public_data'})
                return {'status': True, 'data': data, 'restricted': True,
                        'message': f'Account restricted username : {username}', 'module': 'helper.fetch_public_data'}

            else:
                print({'status': False, 'message': f'Unknown data for username : {username}',
                       'module': 'helper.fetch_public_data'})
                max_retries -= 1
        except Exception as e:
            max_retries -= 1
    if max_retries == 0:
        # print({'status': False, 'message': f"Max tries exceeded! for {username}"})
        return {'status': False, 'message': f"Max tries exceeded! for {username}"}


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
    # if target_username already exists:
    db_result = db['target_usernames'].find_one({'username': username})
    if db_result:
        if 'follower' not in db_result and 'graphql' in db_result:
            db['target_usernames'].update_one({'username': username},
                                              {'$set': {'follower': True, 'updated_at': datetime.datetime.utcnow()}},
                                              upsert=True)
        return {'status': True, 'message': 'User already exists!'}

    result = fetch_public_data(max_retries, username)
    # if data received successfully
    print(result)
    if result['status']:
        data = result['data']
        data['username'] = username
        if 'full' in result:
            data['_id'] = int(data['graphql']['user']['id'])
            data['follower'] = True
        elif 'restricted' in result:
            data['restricted'] = True
        else:
            pass

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
    db_result = db['target_usernames'].find_one({'username': username})
    if db_result:
        if 'following' not in db_result and 'graphql' in db_result:
            db['target_usernames'].update_one({'username': username},
                                              {'$set': {'following': True, 'updated_at': datetime.datetime.utcnow()}},
                                              upsert=True)
        return {'status': True, 'message': 'User already exists!'}

    result = fetch_public_data(max_retries, username)
    # if data received successfully
    print(result)
    if result['status']:
        data = result['data']
        data['username'] = username
        if 'full' in result:
            data['_id'] = int(data['graphql']['user']['id'])
            data['following'] = True
        elif 'restricted' in result:
            data['restricted'] = True
        else:
            pass

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
        send_data_to_wobb(wobb_ep, db_result)
        return

    result = fetch_public_data(max_retries, username)
    # if data received successfully
    if result['status']:
        data = result['data']
        data['username'] = username
        if 'full' in result:
            data['_id'] = data['graphql']['user']['id']
        elif 'restricted' in result:
            data['restricted'] = True
        else:
            pass

        data['created_at'] = datetime.datetime.utcnow()
        data['updated_at'] = datetime.datetime.utcnow()
        db['target_usernames'].insert_one(data)
        send_data_to_wobb(wobb_ep, data)
    else:
        pass
    print(result)
