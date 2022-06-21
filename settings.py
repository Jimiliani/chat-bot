import os
from enum import Enum

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

ACCOUNTS_FILENAME = 'accounts.csv'
LINKS_FILENAME = 'links.csv'

IMAGES_DIRECTORY_NAME = 'images'
ALLOWED_IMAGES_EXTENSIONS = ['jpg', 'jpeg', 'png', 'PNG', 'JPG', 'JPEG']

ASYA_TG_ID = 1593215207
DIMA_TG_ID = 658720016
CHAT_BOT_TG_ID = 1808403369

CHAT_BOT_MESSAGES_TIMEOUT = 180

BASE_URL = 'https://mobileproxy.space/'


class ProxyMethods:
    GET_IP: str = BASE_URL + 'api.html?command=proxy_ip&proxy_id={proxy_id}'
    CHANGE_IP: str = BASE_URL + 'reload.html?proxy_key={proxy_key}&format=json'
    CHANGE_EQUIPMENT: str = BASE_URL + 'api.html?command=change_equipment&proxy_id={proxy_id}'


PROXY_TYPE = 'socks5'
PROXY_ADDR_LIST = [
    '79.143.19.180',
    '193.42.108.148',
    '45.135.132.208',
    '109.172.113.226',
    '45.139.186.61',
    '109.172.7.177',
    '92.62.115.150',
]
PROXY_PORT = 45786
PROXY_USERNAME = os.getenv('PROXY_LOGIN')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
PROXY_RDNS = True
# (айди, хост, порт, логин, пароль, ключ, токен)
MOBILE_PROXIES = [
    (69599, 'bproxy.site', 10749, 'aN7aTn', 'Eh1EcdEEunYm', 'f9533792fc71360ca77b306e94162328', '364eee2ec2ca28fac8bead27c965b411'),
]
ACCOUNTS_ON_PROXY = 7

PROCESS_COUNT = 1

FULL_DIALOG_RETRIES_COUNT = 1
MESSAGE_RETRIES_COUNT = 3

TASK_NAME = None
