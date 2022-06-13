from telethon import TelegramClient
from telethon.sessions import StringSession

import settings


def register_account():
    with TelegramClient(StringSession(), settings.API_ID, settings.API_HASH, proxy=settings.PROXY) as client:
        print(client.session.save())


if __name__ == '__main__':
    register_account()
