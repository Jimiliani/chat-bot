import asyncio
import datetime
import threading

from accounts_parser import AccountsParser
from tg_account import B0TelegramAccount, B1TelegramAccount

import settings
from utils import split_by_chunks, send_reports_to_main_account, send_reports_to_chat_bot


async def main():
    print(datetime.datetime.now())
    parser = AccountsParser(
        settings.ACCOUNTS_FILENAME,
        settings.IMAGES_DIRECTORY_NAME,
        settings.LINKS_FILENAME
    )
    main_accounts = []
    sub_accounts = []
    for acc_data in parser.main_accounts:
        sub_accounts_usernames = list(map(
            lambda sub_account: sub_account['username'],
            parser.sub_accounts_by_main_acc(acc_data)
        ))
        main_acc = B1TelegramAccount(acc_data, sub_accounts_usernames)
        main_accounts.append(main_acc)

        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            sub_accounts.append(B0TelegramAccount(sub_account_data, (await main_acc.id)))

    chunks_with_sub_accounts = split_by_chunks(sub_accounts, settings.THREADS_COUNT)
    threads = []
    for chunk in chunks_with_sub_accounts:
        t = threading.Thread(target=send_reports_to_main_account, args=[chunk])
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    chunks_with_main_accounts = split_by_chunks(main_accounts, settings.THREADS_COUNT)
    threads = []
    for chunk in chunks_with_main_accounts:
        t = threading.Thread(target=send_reports_to_chat_bot, args=[chunk])
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print(datetime.datetime.now())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
