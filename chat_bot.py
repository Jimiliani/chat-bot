import settings


class ChatBotDialog:
    def __init__(self, client):
        self.client = client

    async def get_dialog(self):
        try:
            async with self.client as client:
                return list(
                    filter(
                        lambda dialog: dialog.entity.id == settings.CHAT_BOT_TG_ID,
                        await client.get_dialogs()
                    )
                )[0]
        except IndexError:
            raise RuntimeError(f'Непредвиденная ошибка: не найден диалог с чат ботом')

    async def get_last_message(self):
        return (await self.get_dialog()).message

    async def get_buttons_from_last_message(self):
        return [
            button
            for buttons_group in (await self.get_last_message()).buttons
            for button in buttons_group
        ]

    async def get_buttons_texts(self):
        return '\n'.join(
            map(
                lambda btn: btn.text,
                await self.get_buttons_from_last_message()
            )
        )
