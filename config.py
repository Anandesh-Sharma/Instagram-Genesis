# DB_URI = 'mongodb://deliverate:Rock0004%40@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false'
DB_URI = 'mongodb://root:5bTPa4LNnsI6@65.2.138.79:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false'
# PROXY = {
#     'http': 'http://ishanjindal95:260feb-52c93a-baaaf2-613706-cf77d6@megaproxy.rotating.proxyrack.net:222',
#     'https': 'http://ishanjindal95:260feb-52c93a-baaaf2-613706-cf77d6@megaproxy.rotating.proxyrack.net:222'
# }
PROXY = {
    'http': 'http://geonode_cToIdFQrZL:23097ff4-fb4e-4260-b621-ec0172687250@rotating-residential.geonode.com:222',
    'https': 'http://geonode_cToIdFQrZL:23097ff4-fb4e-4260-b621-ec0172687250@rotating-residential.geonode.com:222'
}


def proxy(country=None):
    if country:
        P_PROXY = {
            'http': f'http://wobb:JWxxRjfpSt6T53DV_country-{country}@proxy.packetstream.io:31112',
            'https': f'http://wobb:JWxxRjfpSt6T53DV_country-{country}@proxy.packetstream.io:31112'
        }
    else:
        P_PROXY = {
            'http': 'http://wobb:JWxxRjfpSt6T53DV@proxy.packetstream.io:31112',
            'https': 'http://wobb:JWxxRjfpSt6T53DV@proxy.packetstream.io:31112'
        }

    return P_PROXY


API_PROXY = 'http://wobb:JWxxRjfpSt6T53DV_country-India@proxy.packetstream.io:31112'
ROOT_USER = 'root'
ROOT_PASS = 'LocalHosting!@675'

"""REDIS CONFIG"""
CELERY_BROKER_URL = 'redis://localhost:6379/0'
RESULT_BACKEND = 'redis://localhost:6379/0'
DAY_LIMIT_PER_ACCOUNT = 30000

"""PROFILE INFO"""
PROFILE = {
    "name": 'Wobb Outreach',
    "website": 'https://wobb.ai/',
    "bio": "Hey Influencers, this is our Influencer outreach account. We don't revert to DMs here. Follow our main Instagram page @wobb.ai for Collabs / Queries",
}

"""
STATUS CODES:
0 - public data extraction failure
1 - failed to send insta dm
"""
