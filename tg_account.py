import socks
import telethon
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.custom import Conversation

import settings
from chat_bot import ChatBot
from utils import safe_get_response, click_button_if_any

TASK_NAME = None


class AbstractTelegramAccount:
    def __init__(self, parser_row, proxy):
        self.username = parser_row['username']
        self.is_main = parser_row['is_main'] == 'TRUE'
        self.session = StringSession(parser_row['hash'])
        self.send_to_username = parser_row['send_to']
        self.image_path = parser_row['image_path']
        self.link = parser_row['link']
        self._proxy = proxy

    @property
    def client(self):
        try:
            return TelegramClient(self.session, settings.API_ID, settings.API_HASH, proxy=self._proxy)
        except Exception as e:
            raise RuntimeError(f'Непредвиденная ошибка при попытке войти в аккаунт {self.username}.')

    @property
    async def id(self):
        async with self.client as client:
            return (await client.get_me()).id


class B0TelegramAccount(AbstractTelegramAccount):
    def __init__(self, parser_row, proxy, main_account_id=None):
        super().__init__(parser_row, proxy)
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
    def __init__(self, parser_row, proxy, sub_accounts_usernames):
        super(B1TelegramAccount, self).__init__(parser_row, proxy)
        self.chat_bot = ChatBot()
        self.sub_accounts_usernames = sub_accounts_usernames

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

    async def send_reports_to_chat_bot(self, retries=settings.FULL_DIALOG_RETRIES_COUNT):
        if not self.is_main:
            raise RuntimeError(f'Не вышло отправить отчеты чат боту: аккаунт `{self.username}` не главный.')

        while retries > 0:
            retries -= 1
            try:
                await self._send_reports_to_chat_bot(self.sub_accounts_usernames)
            except Exception as e:
                print(f'Непредвиденная ошибка: {e}')
        raise ValueError

    @staticmethod
    async def _start_dialog(conv: Conversation):
        await conv.send_message('/start')
        bot_message = await safe_get_response(conv)
        if bot_message.text != 'Привет! Выберите действие из меню!':
            raise RuntimeError(
                f'Неожиданные ответ от чат бота: "{bot_message.text}". '
                f'Ожидалось: \"{"Привет! Выберите действие из меню!"}\"'
            )

    async def _select_task(self, conv: Conversation, client):
        global TASK_NAME
        await conv.send_message('Активные задачи')
        bot_message = await safe_get_response(conv)
        if bot_message.text == 'Нет активных задач':
            raise RuntimeError(f'Нет активных задач для {self.username}')

        buttons_texts = await self.chat_bot.get_buttons_texts(client)
        if TASK_NAME is None:
            print(f'Скопируйте и вставьте задачу из списка:\n{buttons_texts}')
            task_text = str(input())
            TASK_NAME = task_text
            if task_text not in buttons_texts:
                raise RuntimeError(f'Нет задачи с таким текстом')
        else:
            task_text = TASK_NAME
        await bot_message.click(text=task_text)

    async def _send_my_report(self, conv):
        should_send_link = bool(self.link)
        report_saved = False

        bot_message = await safe_get_response(conv)
        clicked = await click_button_if_any(bot_message, 'Свой отчет')
        while not clicked:
            bot_message = await safe_get_response(conv)
            clicked = await click_button_if_any(bot_message, 'Свой отчет')

        while not report_saved:
            bot_message = await safe_get_response(conv)
            if bot_message.text == 'Отправьте изображение выполненной задачи':
                with open(settings.IMAGES_DIRECTORY_NAME + '/' + self.image_path, 'rb') as file:
                    await conv.send_file(file)
            elif bot_message.text == 'Отправьте ссылки':
                if should_send_link:
                    await conv.send_message(str(self.link))
                else:
                    raise RuntimeError('Бот просит ссылку, но у нас её нет')
            elif bot_message.text == 'Перейти к следующему шагу:':
                await click_button_if_any(bot_message, 'К следующему шагу')
            else:
                clicked = await click_button_if_any(bot_message, 'Сохранить отчет')
                if clicked or bot_message.text == 'Отчет к задаче сохранен':
                    report_saved = True
                else:
                    buttons = bot_message.buttons or []
                    raise RuntimeError(
                        f'Непредвиденный ответ от бота, '
                        f'сообщение "{bot_message.text}", '
                        f'кнопки: {list(map(lambda btn: btn.text, buttons))}'
                    )

    async def _send_reports_to_chat_bot(self, sub_accounts_usernames):
        print(f'{self.username} начал отправку отчетов чат боту.')
        should_send_link = bool(self.link)

        async with self.client as client:
            dialog = await self.chat_bot.get_dialog(client)
            messages_to_forward = iter(await self._get_messages_to_forward_to_chat_bot(
                client, sub_accounts_usernames
            ))
            async with client.conversation(dialog) as conv:
                await self._start_dialog(conv)
                await self._select_task(conv, client)
                await self._send_my_report(conv)

                conv.cancel()
                # TODO переделать отправку отчетов за команду, сейчас она отключена
                cycle_len = 3 if should_send_link else 2
                current_cycle_len = cycle_len
                while True:
                    # FIXME здесь нужно также логировать инфу о том, что отчет чела переслан чат боту
                    try:
                        bot_message = await safe_get_response(conv)
                        if 0 < current_cycle_len < cycle_len:
                            message = next(messages_to_forward)
                            await client.forward_message(dialog, message)
                        if current_cycle_len == cycle_len:
                            await bot_message.click(text='За команду')
                            current_cycle_len -= 1
                            continue
                        else:
                            conv.cancel()
                            break
                    except StopIteration:
                        print(f'{self.username} завершил отправку отчетов чат боту')
                        conv.cancel()
                        break
