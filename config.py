DB_URI = 'mongodb://deliverate:Rock0004%40@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false'
PROXY = {
    "http": "http://bobmycity:loxRUFJeBH1r0Shb@proxy.packetstream.io:31112",
    "https": "http://bobmycity:loxRUFJeBH1r0Shb@proxy.packetstream.io:31112"
}
API_PROXY = 'http://bobmycity:loxRUFJeBH1r0Shb@proxy.packetstream.io:31112'
ROOT_USER = 'root'
ROOT_PASS = 'LocalHosting!@675'

"""REDIS CONFIG"""
CELERY_BROKER_URL = 'redis://localhost:6379/0'
RESULT_BACKEND = 'redis://localhost:6379/0'
DAY_LIMIT_PER_ACCOUNT = 30000
