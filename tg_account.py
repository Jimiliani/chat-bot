from typing import Iterable

import telethon
from telethon import TelegramClient, events
from telethon.sessions import StringSession

import settings
from settings import API_ID, API_HASH, DIMA_TG_ID, CHAT_BOT_TG_ID


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
        try:
            return TelegramClient(self.session, API_ID, API_HASH)
        except Exception as e:
            raise RuntimeError(f"Непредвиденная ошибка при попытке войти в аккаунт {self.username}.")

    def get_id(self):
        with self.client as client:
            return client.loop.run_until_complete(client.get_me()).id

    def qwe(self):
        with self.client as client:
            # FIXME удалить
            print(client.get_dialogs())
            # client.loop.run_until_complete(client.get_dialogs())[0].message.buttons

    @staticmethod
    def get_buttons_from_message(message):
        buttons = [button for buttons_group in message.buttons for button in buttons_group]
        return buttons

    @staticmethod
    def get_button_with_text(buttons: Iterable, text: str):
        try:
            return list(
                filter(
                    lambda btn: btn.message == text, buttons
                )
            )[0]
        except IndexError:
            print(f'Непредвиденная ошибка: не найдена кнопка с текстом {text}')

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

    def _get_messages_to_forward_to_chat_bot(self, client, sub_accounts_usernames):
        dialogs_with_sub_accounts = list(
            filter(
                lambda dialog: isinstance(
                    dialog.entity, telethon.tl.types.User
                ) and dialog.entity.username in sub_accounts_usernames,
                client.loop.run_until_complete(client.get_dialogs())
            )
        )
        messages = []
        limit = 2 if self.link else 1
        for dialog in dialogs_with_sub_accounts:
            messages_from_dialog = client.loop.run_until_complete(client.get_messages(dialog, limit=limit))
            messages.extend(list(reversed(messages_from_dialog)))
        return messages

    def send_reports_to_chat_bot(self, sub_accounts_usernames):
        print(f"{self.username} начал отправку отчетов чат боту.")
        if not self.is_main:
            raise ValueError(f"Не вышло отправить отчеты чат боту: аккаунт `{self.username}` не главный.")
        with self.client as client:
            client.loop.run_until_complete(client.send_message(
                CHAT_BOT_TG_ID,
                "/start"
            ))
            self._get_messages_to_forward_to_chat_bot(client, sub_accounts_usernames)

            iterator = iter(self._get_messages_to_forward_to_chat_bot(
                client, sub_accounts_usernames
            ))
            wait_for_tasks = False
            my_report_sent = False
            my_report_image_sent = False
            my_report_link_sent = not self.link
            @client.on(events.NewMessage(from_users=[CHAT_BOT_TG_ID]))
            async def handle_message_from_chat_bot(event):
                bot_message = event.message.message
                nonlocal wait_for_tasks, my_report_sent, my_report_link_sent, my_report_image_sent
                if bot_message == 'Привет! Выберите действие из меню!':
                    await client.send_message(CHAT_BOT_TG_ID, "Активные задачи")
                    wait_for_tasks = True
                    return
                elif wait_for_tasks:
                    buttons_messages = self.get_buttons_from_message(bot_message)
                    buttons_texts = '\n'.join(
                        map(
                            lambda btn: btn.text,
                            buttons_messages
                        )
                    )
                    print(f"Скопируйте и вставьте задачу из списка:\n{buttons_texts}")
                    task_text = str(input())
                    while task_text not in buttons_texts:
                        print('Нет кнопки с таким текстом, попробуйте снова')
                        task_text = str(input())
                    wait_for_tasks = False
                    self.get_button_with_text(buttons_messages, task_text).click()
                    return
                elif not my_report_sent:
                    my_report_sent = True
                    self.get_button_with_text(
                        self.get_buttons_from_message(bot_message),
                        bot_message
                    ).click()
                    return
                elif not my_report_link_sent:
                    my_report_link_sent = True
                    await client.send_message(CHAT_BOT_TG_ID, str(self.link))
                    return
                elif not my_report_image_sent:
                    my_report_image_sent = True
                    file = open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb')
                    await client.send_file(CHAT_BOT_TG_ID, file)
                    file.close()
                    return

                # FIXME здесь нужно также логировать инфу о том, что отчет чела переслан чат боту
                try:
                    message = next(iterator)
                    await client.forward_messages(CHAT_BOT_TG_ID, message)
                except StopIteration:
                    print(f"{self.username} завершил отправку отчетов чат боту")
                    await client.disconnect()

            client.start()
            client.run_until_disconnected()
