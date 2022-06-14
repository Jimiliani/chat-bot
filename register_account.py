import random

from telethon import TelegramClient
from telethon.sessions import StringSession

import settings
import utils


def register_account():
    proxy = random.choice(utils.get_proxies())
    with TelegramClient(StringSession(), settings.API_ID, settings.API_HASH, proxy=proxy) as client:
        print(client.session.save())


if __name__ == '__main__':
    register_account()
