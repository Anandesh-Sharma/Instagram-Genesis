from helper import get_db, fetch_public_data
from fake_useragent import UserAgent
from pymongo import UpdateOne
from threading import Thread
import time
from test import test

db = get_db()
ua = UserAgent()

fetched_data = []
test_run = []


def main(user):
    global fetched_data

    result = fetch_public_data(max_retries=15, username=user['username'])

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

    if 'Max' in result['message']:
        test_run.append(user['_id'])


while True:
    # check if already exists
    st = time.time()
    # work = [i for i in db['users'].find({'public_data': False}, limit=1500)]
    work = []
    for i in test:
        work.append(db['users'].find_one({'_id': i}))

    fs = []
    for i in work:
        fs.append(Thread(target=main, args=(i,)))

    for i in fs:
        i.start()

    for i in fs:
        i.join()
    print('Done')
    result = db['users'].bulk_write(fetched_data, ordered=False)
    with open('test.py', 'w') as f:
        f.write(str(test_run))
    print(result.bulk_api_result)
    fetched_data = []
    print(time.time() - st)
    time.sleep(15)
