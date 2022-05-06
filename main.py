import os

from telethon import TelegramClient


def test():
    with TelegramClient('anon', os.environ.get('API_ID'), os.environ.get(
            'API_HASH')) as client:  # TODO вынести получение этих переменных в отдельные функции
        client.loop.run_until_complete(client.send_message('me', 'Pivo'))


def main():
    send_reports_to_main_account()
    send_to_chat_bot('Здарова')
    wait_chat_bot_to_send('Привет, кидай задачи')
    for i in []:  # список ников пользователей
        forward_last_message_from(i)
        wait_chat_bot_to_send('Норм, ебашь ещё')
    test()


if __name__ == '__main__':
    main()
