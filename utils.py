import asyncio
import random
import traceback
import typing

from telethon.tl.custom import Conversation

import mobile_proxy
import settings


class EmptyResponse:
    text = ''
    buttons = []

    async def click(self, *args, **kwargs):
        return None


async def is_empty(msg):
    return not getattr(msg, 'text', None) and not getattr(msg, 'buttons', None)


async def is_error(msg):
    return 'Возникла непредвиденная ошибка!' in getattr(msg, 'text', '')


async def safe_get_response(conv: Conversation, username, retry=settings.MESSAGE_RETRIES_COUNT):
    empty_messages_in_a_row = 0
    while retry > 0:
        if empty_messages_in_a_row == 3:
            return EmptyResponse()
        retry -= 1
        try:
            msg = await conv.get_response(timeout=settings.CHAT_BOT_MESSAGES_TIMEOUT)
            settings.logging.info(f'[{username}]Сообщение от бота: {msg.text}')
            if await is_empty(msg):
                settings.logging.warning(f'[{username}]Предупреждение: получено сообщение от бота без текста и кнопок.')
                empty_messages_in_a_row += 1
            elif await is_error(msg):
                settings.logging.warning(f'[{username}]Предупреждение: бот говорит, что он сломался.')
            else:
                return msg
            retry += 1
        except (asyncio.exceptions.CancelledError, asyncio.exceptions.TimeoutError):
            pass
    return EmptyResponse()


async def click_button_if_any(msg, text: str) -> bool:
    return bool(await msg.click(text=text))


def split_by_chunks(iterable, proxies):
    chunks = list(map(lambda _: [], range(len(proxies))))
    for instance in iterable:
        chunks[proxies.index(instance._proxy)].append(instance)
    return chunks


def set_completed(username: str, accounts):
    for account in accounts:
        if account.username.lower() == username.lower():
            account.completed = True
            return True
    return False


def send_reports_to_main_account(sub_accounts):
    result = []
    for sub_account in sub_accounts:
        try:
            result.append(
                asyncio.get_event_loop().run_until_complete(
                    sub_account.send_report_to_main_account(),
                )
            )
        except Exception as e:
            settings.logging.error(
                f'[{sub_account.username}]Не удалось отправить отчет для аккаунта {sub_account.username}.\n'
                f'фотка: {sub_account.image_path}\n'
                f'ссылка: {sub_account.link}\n'
            )
            settings.logging.error(
                f'[{sub_account.username}]\n'
                f'username: {sub_account.username}\n'
                f'is_main: {sub_account.is_main}\n'
                f'session: {sub_account.session}\n'
                f'send_to_username: {sub_account.send_to_username}\n'
                f'image_path: {sub_account.image_path}\n'
                f'link: {sub_account.link}\n'
                f'proxy: {sub_account._proxy._as_dict()}\n'
                f'completed: {sub_account.completed}'
            )
            settings.logging.error(f'[{sub_account.username}]{traceback.format_exc()}')
            result.append(f'[{sub_account.username}]' + str(e))
        except asyncio.exceptions.CancelledError:
            pass
    return result


def send_reports_to_chat_bot(main_accounts, task_name, send_for, retries=settings.FULL_DIALOG_RETRIES_COUNT):
    errors = []
    default_retries = retries
    for main_acc in main_accounts:
        remaining_retries = default_retries
        while remaining_retries > 0:
            remaining_retries -= 1
            try:
                result = asyncio.get_event_loop().run_until_complete(
                    main_acc.send_reports_to_chat_bot(task_name, send_for),
                )
                if result:
                    errors.extend(result)
            except Exception as e:
                settings.logging.error(
                    f'[{main_acc.username}]Не удалось отправить отчет для аккаунта {main_acc.username}.\n'
                    f'фотка: {main_acc.image_path}\n'
                    f'ссылка: {main_acc.link}\n'
                )
                settings.logging.error(
                    f'[{main_acc.username}]\n'
                    f'username: {main_acc.username}\n'
                    f'is_main: {main_acc.is_main}\n'
                    f'session: {main_acc.session}\n'
                    f'send_to_username: {main_acc.send_to_username}\n'
                    f'image_path: {main_acc.image_path}\n'
                    f'link: {main_acc.link}\n'
                    f'proxy: {main_acc._proxy._as_dict()}\n'
                    f'completed: {main_acc.completed}'
                )
                settings.logging.error(f'[{main_acc.username}]{traceback.format_exc()}')
                errors.append(f'[{main_acc.username}]' + str(e))
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


def gather_errors(errors: list):
    msg = ''
    for err in errors:
        if isinstance(err, list):
            msg += gather_errors(err)
        elif err:
            msg += err + '\n'
    return msg
