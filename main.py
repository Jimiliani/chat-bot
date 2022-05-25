import asyncio
import datetime

from accounts_parser import AccountsParser
from tg_account import B0TelegramAccount, B1TelegramAccount

import settings


async def main():
    print(datetime.datetime.now())
    parser = AccountsParser(
        settings.ACCOUNTS_FILENAME,
        settings.IMAGES_DIRECTORY_NAME,
        settings.LINKS_FILENAME
    )
    for acc_data in parser.main_accounts:
        main_acc = B1TelegramAccount(acc_data)
        main_acc_id = await main_acc.get_id()
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            sub_account = B0TelegramAccount(sub_account_data, main_acc_id)
            sub_account.send_report_to_main_account()
        sub_accounts_usernames = list(map(
            lambda sub_account: sub_account['username'],
            parser.sub_accounts_by_main_acc(acc_data)
        ))
        try:
            await main_acc.send_reports_to_chat_bot(sub_accounts_usernames, retries=3)
        except ValueError:
            print(
                f'Не удалось отправить отчет для аккаунта {acc_data["username"]}.\n'
            )
            print(f'Изображение: {acc_data["image_path"]}.\n')
            if acc_data['link']:
                print(f'Ссылка: {acc_data["link"]}.\n')
        except asyncio.exceptions.CancelledError:
            pass
    print(datetime.datetime.now())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
