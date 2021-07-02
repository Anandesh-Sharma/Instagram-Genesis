from flask_restful import Resource, reqparse
from helper import get_db, generate_random_hash, fetch_public_data
import requests
import datetime
import json

"""
corresponding ids to request methods.
_id = 1 = add-fake-accounts
_id = 2 = get-public-data
_id = 3 = add-target-username
"""


class AddFakeAccounts(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the username of the fake instagram account', required=True)
        parser.add_argument('password', help='Please add the password of the fake instagram account', required=True)

        data = parser.parse_args()
        username = data['username']
        password = data['password']
        db = get_db()
        job_id = generate_random_hash()
        try:
            db['requests'].insert_one({
                'func': 1,
                'job_id': job_id,
                'stalled': False,
                'args': {
                    'username': username,
                    'password': password
                },
                'created_at': datetime.datetime.utcnow()
            })
            return {'status': True,
                    'message': f'Your request of adding account for username: [{username}] has been submitted successfully!',
                    'job_id': job_id}
        except Exception as e:
            return {'status': False, 'message': f'Error in adding account: {str(e)}'}


class GetPublicData(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the username of the target instagram account', required=True)
        parser.add_argument('host', help='Please add the username of the target instagram account')
        data = parser.parse_args()
        callback_url = None
        print(data)
        if data['host']:
            if requests.get(data['host']).status_code == 200:
                callback_url = data['host']
            else:
                return {'status': False, 'message': 'Host is not valid!'}
        target_username = data['username']
        job_id = generate_random_hash()
        db = get_db()
        try:
            db['requests'].insert_one({
                'func': 2,
                'job_id': job_id,
                'stalled': False,
                'args': {
                    'username': target_username,
                    'callback': callback_url
                },
                'created_at': datetime.datetime.utcnow()
            })
            return {'status': True,
                    'message': f'Your request of public-data for username: [{target_username}] has been submitted successfully!',
                    'job_id': job_id
                    }
        except Exception as e:
            return {'status': False, 'message': f'Error in getting public-data: {str(e)}'}


class AddTargetUsername(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the username of the target instagram account', required=True)
        parser.add_argument('method', help='Please add the method follower/following/all', required=True)
        data = parser.parse_args()
        target_username = data['username']
        method = data['method']
        job_id = generate_random_hash()
        db = get_db()
        try:
            db['requests'].insert_one({
                'func': 3,
                'job_id': job_id,
                'stalled': False,
                'args': {
                    'username': target_username,
                    'method': method
                },
                'created_at': datetime.datetime.utcnow()
            })
            return {'status': True,
                    'message': f'Your request of adding target-username for this username: [{target_username}] has been submitted successfully!',
                    'job_id': job_id}
        except Exception as e:
            return {'status': False, 'message': f'Error in adding target-username: {str(e)}'}


class GetJobResult(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('job_id', help='Please add the parameter job_id', required=True)
        data = parser.parse_args()
        job_id = data['job_id']
        db = get_db()
        try:
            result = db['requests'].find_one({'job_id': job_id})
            if result:
                if result['stalled']:
                    data = json.loads(json.dumps(result, default=str))
                    return {'status': False, 'message': f'Job : {job_id} has been stalled!', 'result': data}
                return {'status': True, 'message': f'Job : {job_id} is still processing!'}
            else:
                return {'status': True, 'message': f'Job : {job_id} is processed successfully!'}
        except Exception as e:
            return {'status': False, 'message': f'Failed to retrieve the data: {e}'}


class SendMessage(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('message', help='Please add the parameter message', required=True)
        parser.add_argument('user_id', help='Please add the parameter user_id', required=True)
        data = parser.parse_args()
        message = data['message']
        user_id = int(data['user_id'])
        job_id = generate_random_hash()
        db = get_db()
        try:
            db['requests'].insert_one({
                'func': 4,
                'job_id': job_id,
                'stalled': False,
                'args': {
                    'user_id': user_id,
                    'message': message
                },
                'created_at': datetime.datetime.utcnow()
            })
            return {'status': True,
                    'message': f'Your request of sending message for this user_id: [{user_id}] has been submitted successfully!',
                    'job_id': job_id}
        except Exception as e:
            return {'status': False, 'message': f'Error in saving your request of sending message for this user_id : [{user_id}]: {str(e)}'}


class GetEmailPhone(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the parameter \'username\'', required=True)
        data = parser.parse_args()
        username = data['username']
        result = fetch_public_data(max_retries=20, username=username)
        if result['status']:
            if 'data' in result:
                if result['data']:
                    return {'status': True,
                            'mobile': result['data']['graphql']['user']['business_phone_number'],
                            'email': result['data']['graphql']['user']['business_email']
                            }
                else:
                    return {'status': True,
                            'mobile': None,
                            'email': None,
                            }
            if 'restricted' in result:
                return {'status': True,
                        'mobile': None,
                        'email': None,
                        }
        else:
            return {
                'status': False,
                'message': 'Max tries exceeded !'
            }


class TestingResource(Resource):
    def get(self):
        return {'message': 'Test Resource'}
