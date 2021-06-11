from helper import get_db
from instagram_private_api.client import Client
import instagram_private_api
from pymongo import InsertOne, UpdateOne
from config import DAY_LIMIT_PER_ACCOUNT
import datetime
import time
import math

db = get_db()

accounts = []


def release_account(username):
    db['accounts'].update_one({'_id': username}, {'$set': {'is_occupied': False}})


def get_accounts():
    global accounts
    accounts = [i for i in get_db()['accounts'].find({}) if
                not i['is_blocked'] and i['fetched'] < DAY_LIMIT_PER_ACCOUNT and not i['is_occupied']]


def account_switcher():
    global step_up_account
    global accounts
    get_accounts()
    while True:
        try:
            if not accounts:
                print("There are no accounts right now")
                time.sleep(600)
            step_up_account += 1
            try:  # if proxy fails then retry on next proxy, don't wanna change account
                api = Client(username=accounts[step_up_account]['_id'],
                             password=accounts[step_up_account]['password'],
                             settings=accounts[step_up_account]['cache_settings'])
                db['accounts'].update_one({'_id': accounts[step_up_account]['_id']}, {'$set': {'is_occupied': True}})
            except instagram_private_api.errors.ClientConnectionError:
                print('Changing proxy for account : {}'.format(accounts[step_up_account]['_id']))
                continue
            break
        except IndexError:
            import traceback
            print(traceback.print_exc())
            print("accounts finished, resetting values : sleeping for 100 seconds")
            get_accounts()
            step_up_account = -1
            time.sleep(100)

        except instagram_private_api.ClientError:
            print(f'Unable to get the client: {accounts[step_up_account]["_id"]}')
            release_account(accounts[step_up_account]['_id'])

        except instagram_private_api.ClientChallengeRequiredError:
            print(f"Account : {accounts[step_up_account]} has been blocked")
            db['accounts'].update_one({'_id': accounts[step_up_account]['_id']}, {'$set': {'is_blocked': True}})
            release_account(accounts[step_up_account]['_id'])
            get_accounts()

    return api


ff_batch_size = 100000
step_up_account = -1

while True:
    target_usernames = db['target_usernames'].find({'follower': True})
    if not target_usernames:
        print('There are no target_usernames')
        time.sleep(10)
        continue
    for t_user in target_usernames:
        followers_done = False
        if 'followers_done' in t_user:
            time.sleep(10)
            continue
        if 'next_cursor' in t_user:
            next_max_id = t_user['next_cursor']
        else:
            next_max_id = None

        user_id = t_user['_id']
        cf_batch_size = 0

        # These variables are specific to accounts which are used to fetch followers
        threshold_step = 10000
        # get rank token, this is the first initialization
        api = account_switcher()
        if not api:
            time.sleep(20)

        rank_token = api.generate_uuid()
        fetched_user_batch = []
        fetched_ids = []
        while cf_batch_size < ff_batch_size:
            st = time.time()
            try:
                if not next_max_id:
                    result = api.user_followers(rank_token=rank_token, user_id=user_id)
                else:
                    result = api.user_followers(rank_token=rank_token, user_id=user_id, max_id=next_max_id)
            except Exception as e:
                print(f'Switching the account because there is some issue with : {api.username}')
                api = account_switcher()
                print(e)
                release_account(accounts[step_up_account]['_id'])
                continue

            print("[FETCHED] --> {} followers".format(len(result['users'])))
            if 'next_max_id' not in result:
                # target_username's followers has been extracted
                followers_done = True
            else:
                next_max_id = result['next_max_id']
                print(next_max_id)
            cf_batch_size += len(result['users'])
            print(f'Current Batch Size : {cf_batch_size}')
            for i in result['users']:
                _id = i['pk']
                if _id not in fetched_ids:
                    fetched_ids.append(_id)
                else:
                    continue
                i['_id'] = _id
                user = db['users'].find_one({'_id': _id})
                if user and '_id' in user:
                    print(f'{_id} exists')

                    if 'follower_rel' in user:
                        if t_user['_id'] not in user['follower_rel']:
                            fetched_user_batch.append(
                                UpdateOne({'_id': _id}, {'$set': {'updated_at': datetime.datetime.utcnow()},
                                                         '$push': {'follower_rel': t_user['_id']}})
                            )
                    else:
                        i['follower_rel'] = [t_user['_id']]

                else:
                    i['follower_rel'] = [t_user['_id']]
                    i['public_data'] = False
                    i['created_at'] = datetime.datetime.utcnow()
                    i['updated_at'] = datetime.datetime.utcnow()
                    i.pop('pk')
                    fetched_user_batch.append(InsertOne(i))

            if len(fetched_user_batch) > threshold_step or followers_done or cf_batch_size > ff_batch_size:
                account = db['accounts'].find_one({'_id': accounts[step_up_account]['_id']})
                db['accounts'].update_one({'_id': accounts[step_up_account]['_id']},
                                          {'$set': {'is_occupied': False,
                                                    'fetched': account['fetched'] + len(fetched_user_batch)}})

                if fetched_user_batch:
                    result = db['users'].bulk_write(fetched_user_batch, ordered=False)
                    print(result.bulk_api_result)
                    fetched_user_batch = []
                    fetched_ids = []
                print(f'Time took for 10K: {time.time() - st}')
                # add next max_id
                if not followers_done:
                    api = account_switcher()
                    db['target_usernames'].update_one({'_id': user_id}, {
                        '$set': {'next_cursor': next_max_id, 'updated_at': datetime.datetime.utcnow()}},
                                                      upsert=True)
                else:
                    db['target_usernames'].update_one({'_id': user_id}, {
                        '$set': {'followers_done': True, 'updated_at': datetime.datetime.utcnow()}},
                                                      upsert=True)
                    break

    time.sleep(20)
