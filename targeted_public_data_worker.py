from helper import get_db, add_following_work, ThreadWithReturnValue, add_follower_work, target_all_work
import time
import datetime

db = get_db()
n_threads = 10
while True:
    requests = [i for i in db['requests'].find({'$and': [{'$or': [{'func': 2}, {'func': 3}]}, {'stalled': False}]})]
    if requests:
        results = []
        threads = []
        for i in requests:
            if i['func'] == 3:
                args = i['args']
                username = args['username']
                if args['method'] == 'following':
                    threads.append((ThreadWithReturnValue(target=add_following_work, args=(username,)), i))
                if args['method'] == 'follower':
                    threads.append((ThreadWithReturnValue(target=add_follower_work, args=(username,)), i))
                if args['method'] == 'all':
                    threads.append((ThreadWithReturnValue(target=target_all_work, args=(username,)), i))

        for t in threads:
            result = t[0].join()
            print(result)
            if not result['status']:
                db['requests'].update_one({'job_id': t[1]}, {'$set': {'stalled': True, 'exception': result['message']}})
            else:
                db['requests'].delete_one({'job_id': t[1]['job_id']})
    else:
        print('No requests')
        time.sleep(20)
