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
