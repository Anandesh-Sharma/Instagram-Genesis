from helper import get_db, store_account, ThreadWithReturnValue
import time

db = get_db()
n_threads = 10
while True:
    requests = [i for i in db['requests'].find({'func': 1, 'stalled': False}, limit=1)]
    if requests:
        results = []
        threads = []
        for i in requests:
            args = i['args']
            username = args['username']
            password = args['password']

            threads.append((ThreadWithReturnValue(target=store_account, args=(username, password,)), i['job_id']))
        for t in threads:
            result = t[0].start()
        for t in threads:
            result = t[0].join()
            print(result)
            if not result['status']:
                db['requests'].update_one({'job_id': t[1]}, {'$set': {'stalled': True, 'exception': result['message']}})
            else:
                db['requests'].delete_one({'job_id': t[1]})

    else:
        print('No accounts requests')
        time.sleep(10)
