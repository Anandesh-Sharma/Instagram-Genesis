from extract_yt_channels import extract
from helper import get_db, ThreadWithReturnValue
import time

db = get_db()
while True:
    requests = [i for i in db['requests'].find({'func': 5, 'stalled': False}, limit=1)]
    if requests:
        results = []
        threads = []
        for i in requests:
            args = i['args']
            keyword = args['keyword']
            message = args['message']

            threads.append((ThreadWithReturnValue(target=extract, args=(keyword, message)), i['job_id']))
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
        print('No youtube requests')
        time.sleep(10)
