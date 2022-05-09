import telethon
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from settings import API_ID, API_HASH, DIMA_TG_ID, ASYA_TG_ID


class TelegramAccount:
    def __init__(self, parser_row):
        self.username = parser_row['username']
        self.is_main = parser_row['is_main'] == 'TRUE'
        self.session = StringSession(parser_row['hash'])
        self.send_to_username = parser_row['send_to']

    @property
    def client(self):
        return TelegramClient(self.session, API_ID, API_HASH)

    def send_report_to_main_account(self):
        print(f"Отправляем отчет от {self.username} к {self.send_to_username}.")
        if self.is_main or not self.send_to_username:
            raise ValueError(
                f"Не вышло отправить отчет главному аккаунту: аккаунт `{self.username}` "
                f"и так главный, либо у него не указано поле `send_to`."
            )
        # FIXME ну это очевидно надо позже поправить на настоящие отчеты
        with self.client as client:
            account_id = client.loop.run_until_complete(client.get_me()).id
            client.loop.run_until_complete(
                client.send_message(DIMA_TG_ID, f"Тест от {self.username}. ID: {account_id}"))

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
