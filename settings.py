import datetime
import logging
import sys

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
    handlers=[
        logging.FileHandler(
            filename=f"logs/{datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.log",
            encoding='utf-8',
            mode='a+'
        )
    ],
    level=logging.DEBUG
)
sys.stdout.reconfigure(encoding='utf-8')

CHAT_BOT_MESSAGES_TIMEOUT = 20


PROXY_TYPE = 'socks5'
PROXY_RDNS = True
# (айди, хост, порт, логин, пароль, ключ, токен)
MOBILE_PROXIES = [
    (93192, 'bproxy.site', 10427, 'tapseN', 'TaEgYF3YhUZU', 'afbedf14b7d655ce05fd567bdd531976', 'e9ae32efffa279374b80482be65c9f82'),
    (93260, 'bproxy.site', 11538, 'YhuS7A', 'eR9gaJYc9ceR', 'b5352f316c0c55ac71aa4414f90237ff', 'b86e7d5a0063bca071f58785bcde1a97'),
    (90066, 'bproxy.site', 11905, 'uN7YB2', 'ED5Ar6ECeD5Y', '7712b1328cd11f42ed641e42a16f76f1', 'abb5140041b69e72d738ddd383a7b42d'),
    (89296, 'eproxy.site', 10496, 'bUKyp5', 'Ar9eMUm4eR9E', '350dcdf19504d7124edb7c32a7d6f6aa', 'ab49106a9b093e39541c9b6b80fda976'),
]
PROCESS_COUNT = len(MOBILE_PROXIES)
PROXY_CHANGE_IP_RETRIES = 1
PROXY_REQUEST_TIMEOUT = 30
ACCOUNTS_ON_PROXY = 10000


FULL_DIALOG_RETRIES_COUNT = 1
MESSAGE_RETRIES_COUNT = 3
