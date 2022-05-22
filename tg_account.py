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

    async def get_id(self):
        async with self.client as client:
            return (await client.get_me()).id


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

    async def _get_messages_to_forward_to_chat_bot(self, client, sub_accounts_usernames):
        # FIXME уродство какое-то
        dialogs_with_sub_accounts = list(
            filter(
                lambda dialog: isinstance(
                    dialog.entity, telethon.tl.types.User
                ) and dialog.entity.username in sub_accounts_usernames,
                await client.get_dialogs()
            )
        )
        messages = []
        limit = 2 if self.link else 1
        for dialog in dialogs_with_sub_accounts:
            messages_from_dialog = await client.get_messages(dialog, limit=limit)
            messages.extend(list(reversed(messages_from_dialog)))
        return messages

    async def send_reports_to_chat_bot(self, sub_accounts_usernames):
        print(f'{self.username} начал отправку отчетов чат боту.')
        if not self.is_main:
            raise RuntimeError(f'Не вышло отправить отчеты чат боту: аккаунт `{self.username}` не главный.')
        dialog = await self.chat_bot_dialog.get_dialog()
        async with self.client as client:
            iterator = iter(await self._get_messages_to_forward_to_chat_bot(
                client, sub_accounts_usernames
            ))
            should_send_link = bool(self.link)
            async with client.conversation(dialog) as conv:
                await conv.send_message('/start')
                bot_message_text = (await conv.get_response()).text
                if bot_message_text != 'Привет! Выберите действие из меню!':
                    raise RuntimeError(
                        f'Неожиданные ответ от чат бота: "{bot_message_text}". '
                        f'Ожидалось: "{"Привет! Выберите действие из меню!"}"'
                    )

                await conv.send_message('Активные задачи')
                bot_message = await conv.get_response()
                if bot_message.text == 'Нет активных задач':
                    raise RuntimeError(f'Нет активных задач для {self.username}')
                buttons_texts = await self.chat_bot_dialog.get_buttons_texts()
                print(f'Скопируйте и вставьте задачу из списка:\n{buttons_texts}')
                task_text = str(input())
                while task_text not in buttons_texts:
                    print('Нет кнопки с таким текстом, попробуйте снова:\n')
                    task_text = str(input())
                await bot_message.click(text=task_text)

                bot_message = await conv.get_response()
                if should_send_link:
                    await conv.send_message(str(self.link))

                bot_message = await conv.get_response()
                with open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb') as file:
                    await conv.send_file(file)

                bot_message = await conv.get_response()
                await bot_message.click(text='Сохранить отчет')

                cycle_len = 3 if should_send_link else 2
                current_cycle_len = cycle_len
                while True:
                    # FIXME здесь нужно также логировать инфу о том, что отчет чела переслан чат боту
                    try:
                        bot_message = await conv.get_response()
                        if 0 < current_cycle_len < cycle_len:
                            message = next(iterator)
                            await client.forward_message(dialog, message)
                        if current_cycle_len == cycle_len:
                            await bot_message.click(text='За команду')
                            current_cycle_len -= 1
                            continue
                        else:
                            current_cycle_len = cycle_len
                            await bot_message.click(text='Сохранить отчет')
                    except StopIteration:
                        print(f'{self.username} завершил отправку отчетов чат боту')
                        conv.cancel()
