import os
from enum import Enum

API_ID = 10690614
API_HASH = '0b44105f7cb2843d07e94535b9c13823'

BASE_URL = 'https://mobileproxy.space/'


class ProxyMethods:
    GET_IP: str = BASE_URL + 'api.html?command=proxy_ip&proxy_id={proxy_id}'
    CHANGE_IP: str = BASE_URL + 'reload.html?proxy_key={proxy_key}&format=json'
    CHANGE_EQUIPMENT: str = BASE_URL + 'api.html?command=change_equipment&proxy_id={proxy_id}'


ACCOUNTS_FILENAME = 'accounts.csv'
LINKS_FILENAME = 'links.csv'

IMAGES_DIRECTORY_NAME = 'images'
ALLOWED_IMAGES_EXTENSIONS = ['jpg', 'jpeg', 'png', 'PNG', 'JPG', 'JPEG']

CHAT_BOT_MESSAGES_TIMEOUT = 180


PROXY_TYPE = 'socks5'
PROXY_RDNS = True
# (айди, хост, порт, логин, пароль, ключ, токен)
MOBILE_PROXIES = [
    (69599, 'bproxy.site', 10749, 'aN7aTn', 'Eh1EcdEEunYm', 'f9533792fc71360ca77b306e94162328', '364eee2ec2ca28fac8bead27c965b411'),
]
ACCOUNTS_ON_PROXY = 57

PROCESS_COUNT = 1

FULL_DIALOG_RETRIES_COUNT = 1
MESSAGE_RETRIES_COUNT = 3
