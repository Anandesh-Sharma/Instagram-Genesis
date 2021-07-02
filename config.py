# DB_URI = 'mongodb://deliverate:Rock0004%40@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false'
DB_URI = 'mongodb://root:5bTPa4LNnsI6@ec2-13-235-54-153.ap-south-1.compute.amazonaws.com:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false'
PROXY = {
    'http': 'http://ishanjindal95:260feb-52c93a-baaaf2-613706-cf77d6@megaproxy.rotating.proxyrack.net:222',
    'https': 'http://ishanjindal95:260feb-52c93a-baaaf2-613706-cf77d6@megaproxy.rotating.proxyrack.net:222'
}
P_PROXY = {
    'http': 'http://wobb:JWxxRjfpSt6T53DV@proxy.packetstream.io:31112',
    'https': 'http://wobb:JWxxRjfpSt6T53DV@proxy.packetstream.io:31112'
}

API_PROXY = 'http://qitchen:KTJxs6nH75brdGtL@proxy.packetstream.io:31112'
ROOT_USER = 'root'
ROOT_PASS = 'LocalHosting!@675'

"""REDIS CONFIG"""
CELERY_BROKER_URL = 'redis://localhost:6379/0'
RESULT_BACKEND = 'redis://localhost:6379/0'
DAY_LIMIT_PER_ACCOUNT = 30000
