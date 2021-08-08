from flask import Flask
from flask_restful import Api
import resources


app = Flask(__name__)
api = Api(app)


api.add_resource(resources.AddFakeAccounts, '/add-fake-account')
api.add_resource(resources.AddTargetUsername, '/add-target-username')
api.add_resource(resources.GetEmailPhone, '/get-email-phone')
api.add_resource(resources.Youtube, '/add-youtube')
api.add_resource(resources.GetPublicData, '/get-public-data')
api.add_resource(resources.SendMessage, '/send-message')
api.add_resource(resources.TestingResource, '/testing')
api.add_resource(resources.GetJobResult, '/get-job')
api.add_resource(resources.AddGmailAccounts, '/add-gmail-account')
