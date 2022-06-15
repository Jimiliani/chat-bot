import settings


class ChatBot:
    @staticmethod
    async def get_dialog(client, username):
        try:
            return next(
                filter(
                    lambda dialog: dialog.entity.id == settings.CHAT_BOT_TG_ID,
                    await client.get_dialogs()
                )
            )
        except StopIteration:
            raise RuntimeError(f'[{username}]Непредвиденная ошибка: не найден диалог с чат ботом')

    async def get_last_message(self, client, username):
        return (await self.get_dialog(client, username)).message

    async def get_buttons_from_last_message(self, client, username):
        return [
            button
            for buttons_group in (await self.get_last_message(client, username)).buttons
            for button in buttons_group
        ]

    async def get_buttons_texts(self, client, username):
        return '\n'.join(
            map(
                lambda btn: btn.text,
                await self.get_buttons_from_last_message(client, username)
            )
        )
