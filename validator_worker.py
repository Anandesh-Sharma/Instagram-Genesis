from helper import get_db
from config import API_PROXY
from instagram_private_api.client import Client
import instagram_private_api as ipa
import time
import datetime

db = get_db()

while True:
    accounts = [i for i in db['accounts'].find({'is_blocked': False})]
    for account in accounts:

        if datetime.datetime.utcnow() > account['cookie_expiry']:
            # its time to refresh the cookie
            try:
                new_client = Client(username=account['username'], password=account['password'], proxy=API_PROXY)
                db['accounts'].update_one({'username': account['username']},
                                          {'$set': {'cache_settings': new_client.settings,
                                                    'cookie_expiry': datetime.datetime.utcfromtimestamp(
                                                        new_client.cookie_jar.auth_expires)}})
                print('Cookies refreshed : {}'.format(account['_id']))
            except ipa.ClientError:
                print(f'Failed to get new cookies for an expired account: {account["_id"]}')
        try:
            api = Client(username=account['username'],
                         password=account['password'],
                         settings=account['cache_settings'],
                         proxy=API_PROXY)
            api.user_followers(11830955, rank_token=api.generate_uuid())
            db['accounts'].update_one({'username': account['username']}, {'$set': {'country': 'India'}}, upsert=True)
            print('Account is valid: {}'.format(account['username']))
            time.sleep(10)
        except ipa.ClientConnectionError:
            pass
        except (ipa.ClientChallengeRequiredError, ipa.ClientCheckpointRequiredError, ipa.ClientLoginRequiredError):
            # set account to unactive
            print(str(account['username']) + 'is blocked')
            db['accounts'].update_one({'username': account['username']}, {'$set': {'is_blocked': True}})
