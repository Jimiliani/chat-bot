from typing import Iterable

import telethon
from telethon import TelegramClient, events
from telethon.sessions import StringSession

import settings
from chat_bot import ChatBotDialog


class AbstractTelegramAccount:
    def __init__(self, parser_row):
        self.username = parser_row['username']
        self.is_main = parser_row['is_main'] == 'TRUE'
        self.session = StringSession(parser_row['hash'])
        self.send_to_username = parser_row['send_to']
        self.image_path = parser_row['image_path']
        self.link = parser_row['link']

    @property
    def client(self):
        try:
            return TelegramClient(self.session, settings.API_ID, settings.API_HASH)
        except Exception as e:
            raise RuntimeError(f'Непредвиденная ошибка при попытке войти в аккаунт {self.username}.')

    def get_id(self):
        with self.client as client:
            return client.loop.run_until_complete(client.get_me()).id


class B0TelegramAccount(AbstractTelegramAccount):
    def __init__(self, parser_row, main_account_id=None):
        super().__init__(parser_row)
        self.main_account_id = main_account_id

    def send_report_to_main_account(self):
        print(f'Отправляем отчет от {self.username} к {self.send_to_username}.')
        if self.is_main or not self.send_to_username:
            raise ValueError(
                f'Не вышло отправить отчет главному аккаунту: аккаунт `{self.username}` '
                f'и так главный, либо у него не указано поле `send_to`.'
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


class B1TelegramAccount(AbstractTelegramAccount):
    def __init__(self, parser_row):
        super(B1TelegramAccount, self).__init__(parser_row)
        self.chat_bot_dialog = ChatBotDialog(self.client)

    def _get_messages_to_forward_to_chat_bot(self, client, sub_accounts_usernames):
        # FIXME уродство какое-то
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
        print(f'{self.username} начал отправку отчетов чат боту.')
        if not self.is_main:
            raise ValueError(f'Не вышло отправить отчеты чат боту: аккаунт `{self.username}` не главный.')
        with self.client as client:
            client.loop.run_until_complete(client.send_message(
                settings.CHAT_BOT_TG_ID,
                '/start'
            ))
            self._get_messages_to_forward_to_chat_bot(client, sub_accounts_usernames)

            iterator = iter(self._get_messages_to_forward_to_chat_bot(
                client, sub_accounts_usernames
            ))
            wait_for_tasks = False
            my_report_sent = False
            my_report_saved = False
            my_report_image_sent = False
            my_report_link_sent = not self.link

            @client.on(events.NewMessage(from_users=[settings.CHAT_BOT_TG_ID]))
            async def handle_message_from_chat_bot(event):
                # FIXME если акк не заведен в чат боте, то он напишет хуйню какую-то, надо об этом уведомлять
                bot_message = event.message.message
                nonlocal wait_for_tasks, my_report_sent, my_report_link_sent, my_report_image_sent, my_report_saved
                # FIXME опять уродство, нужно это как-то поправить
                if bot_message == 'Привет! Выберите действие из меню!':
                    await client.send_message(settings.CHAT_BOT_TG_ID, 'Активные задачи')
                    wait_for_tasks = True
                    return
                elif wait_for_tasks:
                    buttons_texts = self.chat_bot_dialog.get_buttons_texts()
                    print(f'Скопируйте и вставьте задачу из списка:\n{buttons_texts}')
                    task_text = str(input())
                    while task_text not in buttons_texts:
                        print('Нет кнопки с таким текстом, попробуйте снова')
                        task_text = str(input())
                    wait_for_tasks = False
                    self.chat_bot_dialog.get_button_with_text(task_text).click()
                    return
                elif not my_report_sent:
                    my_report_sent = True
                    self.chat_bot_dialog.get_button_with_text('Свой отчет').click()
                    return
                elif not my_report_link_sent:
                    my_report_link_sent = True
                    await client.send_message(settings.CHAT_BOT_TG_ID, str(self.link))
                    return
                elif not my_report_image_sent:
                    my_report_image_sent = True
                    file = open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb')
                    await client.send_file(settings.CHAT_BOT_TG_ID, file)
                    file.close()
                    return
                elif not my_report_saved:
                    my_report_saved = True
                    self.chat_bot_dialog.get_button_with_text('Сохранить отчет').click()
                    return

                # FIXME здесь нужно также логировать инфу о том, что отчет чела переслан чат боту
                try:
                    # FIXME не будет работать, 4 сообщения за раз нам бот от этого отправит
                    self.chat_bot_dialog.get_button_with_text('За команду').click()
                    message = next(iterator)
                    await client.forward_messages(settings.CHAT_BOT_TG_ID, message)
                    if self.link:
                        await client.forward_messages(settings.CHAT_BOT_TG_ID, message)
                    self.chat_bot_dialog.get_button_with_text('Сохранить отчет').click()
                except StopIteration:
                    print(f'{self.username} завершил отправку отчетов чат боту')
                    await client.disconnect()

            client.start()
            client.run_until_disconnected()
