import socks
from telethon import TelegramClient
from telethon.sessions import StringSession

import settings

socks.set_default_proxy(
    socks.SOCKS5,
    settings.PROXY_HOST,
    settings.PROXY_PORT,
    settings.PROXY_LOGIN,
    settings.PROXY_PASSWORD,
)
proxy = socks.get_default_proxy()


def register_account():
    with TelegramClient(StringSession(), settings.API_ID, settings.API_HASH, proxy=proxy) as client:
        print(client.session.save())


if __name__ == '__main__':
    register_account()
