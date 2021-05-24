from helper import get_db, public_user_info


def get_target(username):
    result = public_user_info(username)
    if result['status']:
        public_data = result['data']
    else:
        return result

    # filter the json
    public_data['_id'] = int(public_data['graphql']['user']['id'])
    public_data['username'] = username

    db = get_db()
    db['target_usernames'].insert_one(public_data)

    return {'status': True, 'message': f'Successfully added public data of {username}',
            'module': 'store_target_username.get_target'}
