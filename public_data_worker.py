from helper import get_db
import requests
from fake_useragent import UserAgent
from pymongo import InsertOne, UpdateOne
from threading import Thread
import time
import random
from config import PROXY

db = get_db()
ua = UserAgent()

fetched_data = []


def fetch_public_data(user):
    global fetched_data
    url = f'https://www.instagram.com/{user["username"]}/?__a=1'
    max_retries = 5
    print(f'Started: {user["username"]}')
    while max_retries != 0:

        try:
            headers = {
                'authority': 'www.instagram.com',
                'cache-control': 'max-age=0',
                'sec-ch-ua': f'"Chromium";v=f"9{random.randrange(0, 9)}", " Not A;Brand";v=f"{random.randrange(0, 9)}", "Microsoft Edge";v=f"{random.randrange(0, 9)}"',
                'sec-ch-ua-mobile': '?0',
                'upgrade-insecure-requests': '1',
                'user-agent': ua.random,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
                'cookie': f'mid=YJpPWAAEAAFQ7wlkijMo8albYEx0; ig_did={random.randrange(0, 9)}BC3010{random.randrange(0, 9)}-E3CA-415{random.randrange(0, 9)}-AECD-4A7EFDD6C15{random.randrange(0, 9)}; ig_nrcb=1; csrftoken=dc{random.randrange(0, 9)}QeJJoWGmbla{random.randrange(0, 9)}oYwMXkDgsbnbrXwNm; ds_user_id=58{random.randrange(0, 9)}4891399; sessionid=587489138{random.randrange(0, 9)}%3AChYJGmJzmvjdzz%3A9; shbid=10082; shbts=1621000731.854482; rur=ASH; csrftoken=iAyMcIur7tpPJyseuUZFemBGdtQ0iWcZ; ds_user_id=5874891{random.randrange(0, 9)}99; ig_did=C7AC329F-8103-488{random.randrange(0, 9)}-B05E-A6220145846A; mid=YJpUpAAEAAERM14fCU_ieV4BLtQr; rur=ASH'
            }
            data = requests.get(url=url, headers=headers, proxies=PROXY)
            data = data.json()
            if data == {}:
                fetched_data.append(UpdateOne({'_id': user['_id']},
                                              {'$set': {'public_data': True}},
                                              upsert=True))
                print({'status': False, 'message': f'No data for username : {user["username"]}',
                       'module': 'public_data_worker.fetch_public_data'})
                return

            break
        except:
            max_retries -= 1

    if max_retries == 0:
        print({'status': False, 'message': f"Max tries exceeded! for {user['username']}"})
        return
    try:
        fetched_data.append(UpdateOne({'_id': user['_id']},
                                      {'$set': {'full_info': data['graphql']['user'], 'public_data': True}},
                                      upsert=True))
    except KeyError as e:
        print(f"Key not found in {user['username']}" + str(e))
    print({'status': True, 'message': f'Successsfully added : {user["username"]}', 'module': 'helper.public_user_info'})


while True:
    # check if already exists
    st = time.time()
    work = [i for i in db['users'].find({'public_data': False}, limit=500)]

    fs = []
    for i in work:
        fs.append(Thread(target=fetch_public_data, args=(i,)))

    for i in fs:
        i.start()

    for i in fs:
        i.join()
    print('Done')
    result = db['users'].bulk_write(fetched_data, ordered=False)
    print(result.bulk_api_result)
    fetched_data = []
    print(time.time() - st)
    time.sleep(15)
