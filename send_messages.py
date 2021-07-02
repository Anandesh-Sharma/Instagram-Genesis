from helper import get_db, MessageClient, ThreadWithReturnValue
import time

db = get_db()
limit = 50


def send_message(account, message, user_id):
    api = MessageClient(username=account['_id'], password=account['password'],
                        settings=account['cache_settings'])
    return api.send_message(message, user_id)


while True:
    requests = [i for i in db['requests'].find({'func': 4, 'stalled': False})]
    if not requests:
        print('There are no requests right now!')
        time.sleep(10)
    threads = []
    for request in requests:
        print(f'Processing request: {request["job_id"]}')
        user_id = request['args']['user_id']
        message = request['args']['message']
        account = db['accounts'].find_one({'$and': [{'message_limit': {'$lt': limit}}, {'is_blocked': False}]})
        data = {
            '_id': account['_id'],
            'job_id': request['job_id']
        }
        if not account:
            print('There are not accounts available for sending messages')
            time.sleep(10)
            continue
        threads.append(
            (ThreadWithReturnValue(target=send_message, args=(account, message, user_id,)), data)
        )
    for t in threads:
        t[0].start()
    for t in threads:
        result = t[0].join()
        print(result)
        if not result['status']:
            db['requests'].update_one({'job_id': t[1]['job_id']},
                                      {'$set': {'stalled': True, 'exception': result['response']}})
        else:
            db['accounts'].update_one({'_id': t[1]['_id']}, {'$inc': {'message_limit': 1}})
            db['requests'].delete_one({'job_id': t[1]['job_id']})
