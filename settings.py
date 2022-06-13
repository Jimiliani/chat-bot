import os

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

ACCOUNTS_FILENAME = 'accounts.csv'
LINKS_FILENAME = 'links.csv'

IMAGES_DIRECTORY_NAME = 'images'
ALLOWED_IMAGES_EXTENSIONS = ['jpg', 'jpeg', 'png']

ASYA_TG_ID = 1593215207
DIMA_TG_ID = 658720016
CHAT_BOT_TG_ID = 1808403369

CHAT_BOT_MESSAGES_TIMEOUT = 15

PROXY = {
    'proxy_type': 'socks5',
    'addr': 'bproxy.site',
    'port': 10749,
    'username': os.getenv('PROXY_LOGIN'),
    'password': os.getenv('PROXY_PASSWORD'),
    'rdns': True,
}


THREADS_COUNT = 1
