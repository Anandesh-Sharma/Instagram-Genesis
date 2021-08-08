from helper import get_db, store_gmail_accounts
import time

db = get_db()
n_threads = 1
while True:
    requests = [i for i in db['requests'].find({'func': 6, 'stalled': False}, limit=n_threads)]
    if requests:
        for i in requests:
            args = i['args']
            email = args['email']
            password = args['password']

            store_gmail_accounts(email, password)

            # if not result['status']:
            #     db['requests'].update_one({'job_id': t[1]}, {'$set': {'stalled': True, 'exception': result['message']}})
            # else:
            #     db['requests'].delete_one({'job_id': t[1]})

    else:
        print('No accounts requests')
        time.sleep(10)
