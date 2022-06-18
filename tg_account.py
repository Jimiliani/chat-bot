import traceback

import telethon
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.custom import Conversation
from typing import List

import settings
from chat_bot import ChatBot
from utils import safe_get_response, click_button_if_any


class AbstractTelegramAccount:
    def __init__(self, parser_row, proxy):
        self.username = parser_row['username']
        self.is_main = parser_row['is_main'] == 'TRUE'
        self.session = StringSession(parser_row['hash'])
        self.send_to_username = parser_row['send_to']
        self.image_path = parser_row['image_path']
        self.link = parser_row['link']
        self._proxy = proxy
        self.completed = False

    @property
    def client(self):
        try:
            return TelegramClient(self.session, settings.API_ID, settings.API_HASH, proxy=self._proxy)
        except Exception as e:
            raise RuntimeError(f'[{self.username}]Непредвиденная ошибка при попытке войти в аккаунт {self.username}.')

    @property
    async def id(self):
        async with self.client as client:
            return (await client.get_me()).id


class B0TelegramAccount(AbstractTelegramAccount):
    async def send_report_to_main_account(self):
        print(f'[{self.username}]Отправляем отчет от {self.username} к {self.send_to_username}.')
        if self.is_main or not self.send_to_username:
            raise ValueError(
                f'[{self.username}]Не вышло отправить отчет главному аккаунту: аккаунт `{self.username}` '
                f'и так главный, либо у него не указано поле `send_to`.'
            )
        async with self.client as client:
            entity = await client.get_entity(self.send_to_username)
            if self.link:
                await client.send_message(entity, str(self.link))
            with open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb') as file:
                await client.send_file(entity, file)
        self.completed = True
        print(f'[{self.username}]Отчет от {self.username} к {self.send_to_username} отправлен успешно.')


class B1TelegramAccount(AbstractTelegramAccount):
    def __init__(self, parser_row, proxy, sub_accounts):
        super(B1TelegramAccount, self).__init__(parser_row, proxy)
        self.chat_bot = ChatBot()
        self.sub_accounts: List[B0TelegramAccount] = sub_accounts

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

    @property
    def completed_sub_accounts_usernames(self):
        return list(
            map(
                lambda sub_account: sub_account.username,
                filter(
                    lambda sub_account: sub_account.completed,
                    self.sub_accounts
                )
            )
        )

    async def send_reports_to_chat_bot(self, retries=settings.FULL_DIALOG_RETRIES_COUNT):
        if not self.is_main:
            raise RuntimeError(
                f'[{self.username}]Не вышло отправить отчеты чат боту: аккаунт `{self.username}` не главный.'
            )
        error = ''
        while retries > 0:
            retries -= 1
            try:
                await self._send_reports_to_chat_bot(self.completed_sub_accounts_usernames)
                return
            except Exception as e:
                error = f'[{self.username}]Непредвиденная ошибка: {e}'
                print(error)
                print(f'[{self.username}]{traceback.format_exc()}')
        raise ValueError(error)

    async def _start_dialog(self, conv: Conversation):
        await conv.send_message('/start')
        bot_message = await safe_get_response(conv, self.username)
        if bot_message.text != 'Привет! Выберите действие из меню!':
            raise RuntimeError(
                f'[{self.username}]Неожиданные ответ от чат бота: "{bot_message.text}". '
                f'Ожидалось: \"{"Привет! Выберите действие из меню!"}\"'
            )

    async def _select_task(self, conv: Conversation, client):
        await conv.send_message('Активные задачи')
        bot_message = await safe_get_response(conv, self.username)
        if bot_message.text == 'Нет активных задач':
            raise RuntimeError(f'[{self.username}]Нет активных задач для {self.username}')

        buttons_texts = await self.chat_bot.get_buttons_texts(client, self.username)
        try:
            task_text = next(filter(lambda text: settings.TASK_NAME in text, buttons_texts.split('\n')))
        except StopIteration:
            raise RuntimeError(f'[{self.username}]Нет задачи с текстом {settings.TASK_NAME}.')
        await bot_message.click(text=task_text)

    async def _send_my_report(self, conv):
        should_send_link = bool(self.link)
        report_saved = False

        bot_message = await safe_get_response(conv, self.username)
        clicked = await click_button_if_any(bot_message, 'Свой отчет')
        while not clicked:
            bot_message = await safe_get_response(conv, self.username)
            clicked = await click_button_if_any(bot_message, 'Свой отчет')

        while not report_saved:
            bot_message = await safe_get_response(conv, self.username)
            if bot_message.text == 'Отправьте изображение выполненной задачи':
                with open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb') as file:
                    await conv.send_file(file)
            elif bot_message.text == 'Отправьте ссылки':
                if should_send_link:
                    await conv.send_message(str(self.link))
                else:
                    raise RuntimeError(f'[{self.username}]Бот просит ссылку, но у нас её нет')
            elif bot_message.text == 'Перейти к следующему шагу:':
                await click_button_if_any(bot_message, 'К следующему шагу')
                await click_button_if_any(bot_message, 'Сохранить отчет')
            else:
                clicked = await click_button_if_any(bot_message, 'Сохранить отчет')
                if clicked or bot_message.text == 'Отчет к задаче сохранен':
                    report_saved = True
                    print(f'[{self.username}]Отчет за {self.username} сохранен')
                else:
                    buttons = bot_message.buttons or []
                    raise RuntimeError(
                        f'[{self.username}]Непредвиденный ответ от бота, '
                        f'сообщение "{bot_message.text}", '
                        f'кнопки: {list(map(lambda btn: btn.text, buttons))}'
                    )

    async def _send_reports_to_chat_bot(self, sub_accounts_usernames):
        print(f'[{self.username}]{self.username} начал отправку отчетов чат боту.')
        should_send_link = bool(self.link)

        async with self.client as client:
            dialog = await self.chat_bot.get_dialog(client, self.username)
            messages_to_forward = iter(await self._get_messages_to_forward_to_chat_bot(
                client, sub_accounts_usernames
            ))
            async with client.conversation(dialog) as conv:
                await self._start_dialog(conv)
                await self._select_task(conv, client)
                await self._send_my_report(conv)

                members_left = len(sub_accounts_usernames)
                while members_left > 0:
                    members_left -= 1
                    await self._start_dialog(conv)
                    await self._select_task(conv, client)

                    report_saved = False
                    bot_message = await safe_get_response(conv, self.username)
                    clicked = await click_button_if_any(bot_message, 'За команду')
                    while not clicked:
                        bot_message = await safe_get_response(conv, self.username)
                        clicked = await click_button_if_any(bot_message, 'За команду')

                    while not report_saved:
                        bot_message = await safe_get_response(conv, self.username)
                        if bot_message.text == 'Отправьте изображение выполненной задачи':
                            message = next(messages_to_forward)
                            await client.forward_messages(dialog, message)
                        elif bot_message.text == 'Отправьте ссылки':
                            if should_send_link:
                                message = next(messages_to_forward)
                                await client.forward_messages(dialog, message)
                            else:
                                raise RuntimeError(f'[{self.username}]Бот просит ссылку, но у нас её нет')
                        elif bot_message.text == 'Перейти к следующему шагу:':
                            await click_button_if_any(bot_message, 'К следующему шагу')
                            await click_button_if_any(bot_message, 'Сохранить отчет')
                        else:
                            clicked = await click_button_if_any(bot_message, 'Сохранить отчет')
                            if clicked or bot_message.text == 'Отчет к задаче сохранен':
                                report_saved = True
                                print(f'[{self.username}]Отчет за члена команды сохранен')
                            else:
                                buttons = bot_message.buttons or []
                                raise RuntimeError(
                                    f'[{self.username}]Непредвиденный ответ от бота, '
                                    f'сообщение "{bot_message.text}", '
                                    f'кнопки: {list(map(lambda btn: btn.text, buttons))}'
                                )
                conv.cancel()
