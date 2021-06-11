from helper import get_db, add_following_work, ThreadWithReturnValue, add_follower_work, target_all_work, only_public_data
import time

db = get_db()
n_threads = 500
while True:
    requests = [i for i in db['requests'].find({'$and': [{'$or': [{'func': 2}, {'func': 3}]}, {'stalled': False}]}, limit=n_threads)]
    if requests:
        threads = []
        for i in requests:
            args = i['args']
            username = args['username']
            if i['func'] == 3:
                if args['method'] == 'following':
                    print(f'Got new following request: {username}')
                    threads.append((ThreadWithReturnValue(target=add_following_work, args=(username,)), i))
                if args['method'] == 'follower':
                    print(f'Got new follower request: {username}')
                    threads.append((ThreadWithReturnValue(target=add_follower_work, args=(username,)), i))
                if args['method'] == 'all':
                    print(f'Got new following and follower request: {username}')
                    threads.append((ThreadWithReturnValue(target=target_all_work, args=(username,)), i))

            if i['func'] == 2:
                callback = args['callback']
                print(f'Got new only public data request: {username}')
                threads.append((ThreadWithReturnValue(target=only_public_data, args=(username, callback,)), i))

        for t in threads:
            result = t[0].join()
            print(result)
            if not result['status']:
                db['requests'].update_one({'job_id': t[1]['job_id']}, {'$set': {'stalled': True, 'exception': result['message']}})
            else:
                db['requests'].delete_one({'job_id': t[1]['job_id']})
    else:
        print('No requests')
        time.sleep(20)
