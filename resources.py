from flask_restful import Resource, reqparse
from helper import get_db, generate_random_hash
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
        if requests.get(data['host']).status_code == 200:
            url = data['host']
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
                    'callback': url
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


class TestingResource(Resource):
    def get(self):
        return {'message': 'Test Resource'}
