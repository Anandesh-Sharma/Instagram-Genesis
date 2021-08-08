import time
from concurrent.futures import ThreadPoolExecutor
from seleniumwire import webdriver
from config import PROXY
from selenium.webdriver.chrome.options import Options
from helper import get_db


# TODO : some people has added only https://instagram.com which is a case to be handled
def get_browser(url):
    sw_options = {
        'proxy': PROXY
    }
    while True:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        try:
            browser = webdriver.Chrome(options=options)
            browser.get(url)
            break
        except:
            pass

    return browser


db = get_db()
format_url1 = 'https://www.youtube.com/channel/{}'
format_url2 = 'https://www.youtube.com/{}'


# print(channels)

def extract(channel_id):
    print(channel_id + 'Started')
    social_handle = {}

    def check_social_platform(link):
        if 'instagram' in link:
            social_handle['instagram'] = link
        elif 'facebook' in link:
            social_handle['facebook'] = link
        elif 'twitter' in link:
            social_handle['twitter'] = link
        elif 'tiktok' in link:
            social_handle['tiktok'] = link
        elif 'patreon' in link:
            social_handle['patreon'] = link
        elif 'twitch' in link:
            social_handle['twitch'] = link
        else:
            if 'unknown' in social_handle:
                social_handle['unknown'].append(link)
            else:
                social_handle['unknown'] = [link]

    def fetch_social_handles(url):
        browser = get_browser(url)
        try:
            primary_link = \
                browser.find_element_by_xpath('//div[@id="primary-links"]/a').get_attribute('href').split('=')[-1]
            primary_link = primary_link.replace('%3A', ':').replace('%2F', '/').replace('%3D', '=').replace('%3F', '?')
            check_social_platform(primary_link)
        except:
            print('No primary links found on {}'.format(channel_id))
        try:
            secondary_links = browser.find_elements_by_xpath('//div[@id="secondary-links"]/a')
            for i in secondary_links:
                link = i.get_attribute('href').split('=')[-1].replace('%3A', ':').replace('%2F', '/').replace('%3D',
                                                                                                              '=').replace(
                    '%3F', '?')
                check_social_platform(link)
        except:
            print('No secondary links found on {}'.format(channel_id))

        browser.quit()

    if channel_id[0] == 'U' and len(channel_id) == 24:
        fetch_social_handles(format_url1.format(channel_id))
    else:
        fetch_social_handles(format_url2.format(channel_id))

    if 'instagram' in social_handle:
        db['youtube'].update_one({'_id': channel_id},
                                 {'$set': {'insta_dm': False}}, upsert=True)
    db['youtube'].update_one({'_id': channel_id},
                                 {'$set': {'social_handles': social_handle}})
    print(social_handle)


while True:
    channels = db['youtube'].find({'social_handles': {"$exists": False}})
    treads = []
    if not channels:
        print('No channels are left!')
        time.sleep(10)
    channel_ids = [i['_id'] for i in channels]

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(extract, channel_ids)
