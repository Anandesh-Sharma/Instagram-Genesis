from helper import get_db, fetch_public_data
from fake_useragent import UserAgent
from pymongo import UpdateOne
from concurrent.futures import ThreadPoolExecutor
import time
import requests

db = get_db()
ua = UserAgent()

fetched_data = []
test_run = []


def main(user):
    global fetched_data

    result = fetch_public_data(max_retries=13, username=user['username'])

    if result['status']:
        # print(result['message'])
        if 'restricted' in result:
            fetched_data.append(UpdateOne({'_id': user['_id']},
                                          {'$set': {'restricted': True, 'public_data': True}},
                                          upsert=True))
        else:

            fetched_data.append(UpdateOne({'_id': user['_id']},
                                          {'$set': {'public_data': True, 'full_info': result['data']}},
                                          upsert=True))
    else:
        print(result['message'])


if __name__ == '__main__':
    while True:
        st = time.time()
        work = [i for i in db['users'].find({'public_data': False}, limit=100)]

        with ThreadPoolExecutor() as executor:
            executor.map(main, work)

        print('Done')
        try:
            result = db['users'].bulk_write(fetched_data, ordered=False)
        except:
            time.sleep(10)
            continue

        print(result.bulk_api_result)
        t = time.time() - st

        print(t)
        url = "https://api.telegram.org/bot1612075455:AAGEMj6Fbc63A0aaiFxTLFKktcbxb45YMW8/sendMessage?chat_id=772146169&text=Time took : {} for {}".format(
            t, len(fetched_data))

        requests.get(url)
        fetched_data = []
        time.sleep(15)
