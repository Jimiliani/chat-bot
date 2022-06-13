import asyncio

from telethon.tl.custom import Conversation

import settings


class EmptyResponse:
    text = None

    def click(self):
        return None


async def safe_get_response(conv: Conversation, retry=3):
    while retry > 0:
        retry -= 1
        try:
            return await conv.get_response(timeout=settings.CHAT_BOT_MESSAGES_TIMEOUT)
        except asyncio.exceptions.CancelledError:
            pass
    return EmptyResponse()


async def click_button_if_any(msg, text: str) -> bool:
    return bool(msg.click(text=text))


async def split_by_chunks(iterable, chunks_count):
    chunk_size = len(iterable) // chunks_count + min(len(iterable) % chunks_count, 1)
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i + chunk_size]


def send_reports_to_main_account(sub_accounts):
    for sub_account in sub_accounts:
        sub_account.send_report_to_main_account()


def send_reports_to_chat_bot(main_accounts):
    for main_acc in main_accounts:
        try:
            await main_acc.send_reports_to_chat_bot(retries=3)
        except ValueError:
            print(
                f'Не удалось отправить отчет для аккаунта {main_acc.username}.\n'
            )
            print(f'Изображение: {main_acc.image_path}.\n')
            if main_acc.link:
                print(f'Ссылка: {main_acc.link}.\n')
        except asyncio.exceptions.CancelledError:
            pass
