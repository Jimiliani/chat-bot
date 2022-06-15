import asyncio
import traceback
import typing

from telethon.tl.custom import Conversation

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
            if is_empty(msg):
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
    errors =  []
    for sub_account in sub_accounts:
        try:
            asyncio.run(sub_account.send_report_to_main_account())
        except ValueError as e:
            print(
                f'[{sub_account.username}]Не удалось отправить отчет для аккаунта {sub_account.username}.'
            )
            if sub_account.link:
                print(f'[{sub_account.username}]Ссылка: {sub_account.link}.')
            print(f'[{sub_account.username}]Изображение: {sub_account.image_path}.\n')
            print(f'[{sub_account.username}]{traceback.format_exc()}')
            errors.append(str(e))
        except asyncio.exceptions.CancelledError:
            pass
    return errors


def send_reports_to_chat_bot(main_accounts):
    errors = []
    for main_acc in main_accounts:
        try:
            asyncio.run(main_acc.send_reports_to_chat_bot())
        except ValueError as e:
            print(
                f'[{main_acc.username}]Не удалось отправить отчет для аккаунта {main_acc.username}.\n'
            )
            print(f'[{main_acc.username}]Изображение: {main_acc.image_path}.\n')
            if main_acc.link:
                print(f'[{main_acc.username}]Ссылка: {main_acc.link}.\n')
            errors.append(str(e))
        except asyncio.exceptions.CancelledError:
            pass
    return errors


def get_proxies() -> typing.List[dict]:
    return [
        {
            'proxy_type': settings.PROXY_TYPE,
            'addr': proxy_addr,
            'port': settings.PROXY_PORT,
            'username': settings.PROXY_USERNAME,
            'password': settings.PROXY_PASSWORD,
            'rdns': settings.PROXY_RDNS,
        } for proxy_addr in settings.PROXY_ADDR_LIST
    ] * settings.ACCOUNTS_ON_PROXY
