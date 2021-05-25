from flask_restful import Resource, reqparse
from helper import store_account, public_user_info
from redis.client import Redis
from redis import BlockingConnectionPool
import json

client = Redis(connection_pool=BlockingConnectionPool())


class AddFakeAccounts(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the username of the fake instagram account', required=True)
        parser.add_argument('password', help='Please add the password of the fake instagram account', required=True)

        data = parser.parse_args()
        username = data['username']
        password = data['password']

        result = store_account.delay(username=username, password=password)

        return {'status': True, 'message': 'your job is submitted', 'job_id': result.id}


class GetPublicData(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the username of the target instagram account', required=True)

        data = parser.parse_args()
        target_username = data['username']
        r = public_user_info.delay(target_username, add_target_username=False)
        return {'status': True, 'message': 'your job is submitted', 'job_id': r.id}


class AddTargetUsername(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='Please add the username of the target instagram account', required=True)

        data = parser.parse_args()
        target_username = data['username']
        r = public_user_info.delay(target_username)
        return {'status': True, 'message': 'your job is submitted', 'job_id': r.id}


class GetJobResult(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('job_id', help='Please add the parameter job_id', required=True)
        data = parser.parse_args()
        job_id = data['job_id']
        try:
            job = f"celery-task-meta-{job_id}"
            x = client.get(job)
            if x:
                return json.loads(x.decode('utf-8'))
            else:
                return {'status': True, 'message': f'Job : {job_id} is still processing'}
        except Exception as e:
            return {'status': False, 'message': f'Failed to retrieve the data from redis: {e}'}


class TestingResource(Resource):
    def get(self):
        return {'message': 'Test Resource'}
