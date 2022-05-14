import telethon
from telethon import TelegramClient, events
from telethon.sessions import StringSession

import settings
from settings import API_ID, API_HASH, DIMA_TG_ID, ASYA_TG_ID


class TelegramAccount:
    def __init__(self, parser_row, main_account_id=None):
        self.username = parser_row['username']
        self.is_main = parser_row['is_main'] == 'TRUE'
        self.session = StringSession(parser_row['hash'])
        self.send_to_username = parser_row['send_to']
        self.image_path = parser_row['image_path']
        self.link = parser_row['link']
        self.main_account_id = main_account_id

    @property
    def client(self):
        return TelegramClient(self.session, API_ID, API_HASH)

    def get_id(self):
        with self.client as client:
            return client.loop.run_until_complete(client.get_me()).id

    def send_report_to_main_account(self):
        print(f"Отправляем отчет от {self.username} к {self.send_to_username}.")
        if self.is_main or not self.send_to_username:
            raise ValueError(
                f"Не вышло отправить отчет главному аккаунту: аккаунт `{self.username}` "
                f"и так главный, либо у него не указано поле `send_to`."
            )
        with self.client as client:
            if self.link:
                client.loop.run_until_complete(
                    client.send_message(self.main_account_id, str(self.link))
                )
            file = open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb')
            client.loop.run_until_complete(
                client.send_file(self.main_account_id, file)
            )
            file.close()

    def send_reports_to_chat_bot(self, sub_accounts_usernames):
        print(f"{self.username} начал отправку отчетов чат боту.")
        if not self.is_main:
            raise ValueError(f"Не вышло отправить отчеты чат боту: аккаунт `{self.username}` не главный.")
        # FIXME ну тут тоже очевидно не так все должно быть
        with self.client as client:
            client.loop.run_until_complete(client.send_message(
                ASYA_TG_ID,
                "Это типа ты чат бот и я начинаю с тобой диалог. Отправь мне что угодно и я перешлю тебе сообщение от другого аккаунта"
            ))

            # FIXME это стоит вынести в отдельный метод какой-то
            # FIXME в случае со ссылками нам надо 2 последних сообщений отправлять, причем по очереди
            dialogs_with_sub_accounts = list(
                filter(
                    lambda dialog: isinstance(dialog.entity,
                                              telethon.tl.types.User) and dialog.entity.username in sub_accounts_usernames,
                    client.loop.run_until_complete(client.get_dialogs())
                )
            )
            iterator = iter(dialogs_with_sub_accounts)

            @client.on(events.NewMessage(from_users=[DIMA_TG_ID]))
            async def handle_message_from_chat_bot(event):
                # FIXME здесь нужно также логировать инфу о том, что отчет чела переслан чат боту
                try:
                    dialog = next(iterator)
                except StopIteration:
                    print(f"{self.username} завершил отправку отчетов чат боту")
                    # FIXME ну здесь это не катит, потому что аккаунтов главных несколько
                    exit(0)
                await client.forward_messages(ASYA_TG_ID, dialog.message)

            client.start()
            client.run_until_disconnected()
