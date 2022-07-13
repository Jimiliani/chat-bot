import datetime
import logging

API_ID = 10690614
API_HASH = '0b44105f7cb2843d07e94535b9c13823'

CHAT_BOT_TG_ID = 1808403369

BASE_URL = 'https://mobileproxy.space/'


class ProxyMethods:
    GET_IP: str = BASE_URL + 'api.html?command=proxy_ip&proxy_id={proxy_id}'
    CHANGE_IP: str = BASE_URL + 'reload.html?proxy_key={proxy_key}&format=json'
    CHANGE_EQUIPMENT: str = BASE_URL + 'api.html?command=change_equipment&proxy_id={proxy_id}'


ACCOUNTS_FILENAME = 'accounts.csv'
LINKS_FILENAME = 'links.csv'
IMAGES_DIRECTORY_NAME = 'images'
ALLOWED_IMAGES_EXTENSIONS = ['jpg', 'jpeg', 'png', 'PNG', 'JPG', 'JPEG']


logging.basicConfig(
    filename=f"logs/{datetime.datetime.now().strftime('%Y:%m:%d %H:%M:%S')}.log",
    level=logging.DEBUG
)


CHAT_BOT_MESSAGES_TIMEOUT = 30


PROXY_TYPE = 'socks5'
PROXY_RDNS = True
# (айди, хост, порт, логин, пароль, ключ, токен)
MOBILE_PROXIES = [
    (93192, 'bproxy.site', 10427, 'tapseN', 'TaEgYF3YhUZU', 'afbedf14b7d655ce05fd567bdd531976', 'e9ae32efffa279374b80482be65c9f82'),
]
PROXY_CHANGE_IP_RETRIES = 1
PROXY_REQUEST_TIMEOUT = 30
ACCOUNTS_ON_PROXY = 10000

PROCESS_COUNT = 1

FULL_DIALOG_RETRIES_COUNT = 1
MESSAGE_RETRIES_COUNT = 3
