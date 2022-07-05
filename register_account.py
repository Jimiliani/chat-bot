import random

from telethon import TelegramClient
from telethon.sessions import StringSession

import settings
import utils


def register_account():
    proxy = random.choice(utils.get_proxies())
    with TelegramClient(StringSession(), settings.API_ID, settings.API_HASH, proxy=proxy.as_dict()) as client:
        print(client.session.save())
    print('Меняем айпи прокси после входа в аккаунт')
    proxy.change_ip()


if __name__ == '__main__':
    register_account()
