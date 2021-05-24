import instagram_private_api.errors
from instagram_private_api.client import Client
from instagram_private_api.compat import compat_urllib_request
from pymongo import MongoClient
from fake_useragent import UserAgent
import urllib.request
from config import *
import sys
import codecs
import datetime
import requests
from pytz import timezone
from celery import Celery

# useragents
ua = UserAgent()

client = Celery('helper', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')


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


def store_account(username: str, password: str) -> dict:
    """
    :param password:
    :param username:
    :param api: is an instance of instagram_private_api
    :return: dict of results
    """
    db = get_db()

    try:
        api = Client(username=username, password=password)
    except Exception as e:
        return {'status': False, 'message': f'Error in getting the client for {username} : {e}',
                'module': 'helper.store_account'}

    # check if the username already exists
    found = True if db['accounts'].find_one({'_id': api.username}) else False
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
    else:
        return {'status': False, 'message': f'Account already exists: {api.username}', 'module': 'helper.store_account'}


def proxy_support(country=None):
    if country:
        proxy_address = f'http://bobmycity:loxRUFJeBH1r0Shb_country-{country}@proxy.packetstream.io:31112'
    else:
        proxy_address = 'http://bobmycity:loxRUFJeBH1r0Shb@proxy.packetstream.io:31112'

    proxy_handler = compat_urllib_request.ProxyHandler({'https': proxy_address})
    return proxy_handler


@client.task
def public_following(username):
    # TODO : There is still need of little tweak here, as if account is blocked ?
    db = get_db()
    accounts = [i for i in db['accounts'].find({}) if
                not i['is_blocked'] and i['fetched'] < DAY_LIMIT_PER_ACCOUNT and not i['is_occupied']]
    if not accounts:
        return {'status': False, 'message': 'No accounts are present at the moment'}
    while True:
        try:
            api = Client(username=accounts[0]['_id'],
                         password=accounts[0]['password'],
                         settings=accounts[0]['cache_settings'])
            break
        except instagram_private_api.errors.ClientChallengeRequiredError:
            print(f"Account : {accounts[0]} has been blocked")
            db['accounts'].update_one({'_id': accounts[0]['_id']}, {'$set': {'is_blocked': True}})

    api



@client.task()
def public_user_info(username, store=True):
    db = get_db()
    # check if already exists
    username_found = db['target_usernames'].find_one({'username': username})
    if username_found:
        return {'status': False, 'message': 'User already exists!', 'module': 'helper.public_user_info',
                'user_info': username_found}

    url = f'https://www.instagram.com/{username}/?__a=1'
    max_retries = 20
    headers = {
        'authority': 'www.instagram.com',
        'cache-control': 'max-age=0',
        'sec-ch-ua-mobile': '?0',
        'upgrade-insecure-requests': '1',
        'user-agent': ua.random,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.instagram.com/',
        'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
        # 'cookies': 'csrftoken=iAyMcIur7tpPJyseuUZFemBGdtQ0iWcZ; ds_user_id=5874891389; ig_did=C7AC329F-8103-4888-B05E-A6220145846A; mid=YJpUpAAEAAERM14fCU_ieV4BLtQr'
    }
    while max_retries != 0:
        try:
            data = requests.get(url=url, headers=headers, proxies=PROXY).json()
            if not data:
                return {'status': False, 'message': f'No data for username : {username}',
                        'module': 'helper.public_user_info'}

            break
        except:
            max_retries -= 1

    if max_retries == 0:
        return {'status': False, 'message': "Max tries exceeded!"}

    if store:
        data['_id'] = int(data['graphql']['user']['id'])
        data['username'] = username

        db['target_usernames'].insert_one(data)

    return {'status': True, 'message': 'Success', 'module': 'helper.public_user_info', 'user_info': data}
