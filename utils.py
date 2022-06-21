import asyncio
import random
import traceback
import typing

from telethon.tl.custom import Conversation

import mobile_proxy
import settings


# примерно половину этой хуйни можно перетащить в другие файлы и улучшить этим читаемость


class EmptyResponse:
    text = None

    def click(self, *args, **kwargs):
        return None


async def is_empty(msg):
    return not getattr(msg, 'text', None) and not getattr(msg, 'buttons', None)


async def safe_get_response(conv: Conversation, username, retry=settings.MESSAGE_RETRIES_COUNT):
    empty_messages_in_a_row = 0
    while retry > 0:
        if empty_messages_in_a_row == 3:
            return EmptyResponse()
        retry -= 1
        try:
            msg = await conv.get_response(timeout=settings.CHAT_BOT_MESSAGES_TIMEOUT)
            if await is_empty(msg):
                print(f'[{username}]Предупреждение: получено сообщение от бота без текста и кнопок.')
                empty_messages_in_a_row += 1
                retry += 1
                continue
            return msg
        except (asyncio.exceptions.CancelledError, asyncio.exceptions.TimeoutError):
            pass
    return EmptyResponse()


async def click_button_if_any(msg, text: str) -> bool:
    return bool(await msg.click(text=text))


def split_by_chunks(iterable, chunks_count):
    chunk_size = len(iterable) // chunks_count + min(len(iterable) % chunks_count, 1)
    chunk_size = max(chunk_size, 1)
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i + chunk_size]


def send_reports_to_main_account(sub_accounts):
    result = []
    for sub_account in sub_accounts:
        try:
            result.append(asyncio.run(sub_account.send_report_to_main_account()))
        except Exception as e:
            print(f'[{sub_account.username}]Не удалось отправить отчет для аккаунта {sub_account.username}.')
            print(
                f'[{sub_account.username}]\n'
                f'username: {sub_account.username}\n'
                f'is_main: {sub_account.is_main}\n'
                f'session: {sub_account.session}\n'
                f'send_to_username: {sub_account.send_to_username}\n'
                f'image_path: {sub_account.image_path}\n'
                f'link: {sub_account.link}\n'
                f'proxy: {sub_account._proxy.as_dict()}\n'
                f'completed: {sub_account.completed}'
            )
            print(f'[{sub_account.username}]{traceback.format_exc()}')
            result.append(str(e))
        except asyncio.exceptions.CancelledError:
            pass
    return result


def send_reports_to_chat_bot(main_accounts):
    errors = []
    for main_acc in main_accounts:
        try:
            asyncio.run(main_acc.send_reports_to_chat_bot())
        except Exception as e:
            print(f'[{main_acc.username}]Не удалось отправить отчет для аккаунта {main_acc.username}.')
            print(
                f'[{main_acc.username}]\n'
                f'username: {main_acc.username}\n'
                f'is_main: {main_acc.is_main}\n'
                f'session: {main_acc.session}\n'
                f'send_to_username: {main_acc.send_to_username}\n'
                f'image_path: {main_acc.image_path}\n'
                f'link: {main_acc.link}\n'
                f'proxy: {main_acc._proxy.as_dict()}\n'
                f'completed: {main_acc.completed}'
            )
            print(f'[{main_acc.username}]{traceback.format_exc()}')
            errors.append(str(e))
        except asyncio.exceptions.CancelledError:
            pass
    return errors


def get_proxies() -> typing.List[mobile_proxy.MobileProxy]:
    return [
               mobile_proxy.MobileProxy(
                   id_,
                   host,
                   port,
                   login,
                   password,
                   key,
                   token
               )
               for id_, host, port, login, password, key, token in settings.MOBILE_PROXIES
           ]


def get_time_to_sleep():
    return round(random.uniform(1, 3), 2)
