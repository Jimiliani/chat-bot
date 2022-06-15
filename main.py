import asyncio
import datetime
from multiprocessing import Pool

import utils
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
    proxies = iter(utils.get_proxies())
    for acc_data in parser.main_accounts:
        sub_accounts_usernames = list(map(
            lambda sub_account: sub_account['username'],
            parser.sub_accounts_by_main_acc(acc_data)
        ))
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            proxy = next(proxies)
            sub_accounts.append(B0TelegramAccount(sub_account_data, proxy))
        proxy = next(proxies)
        main_acc = B1TelegramAccount(acc_data, proxy, sub_accounts)
        main_accounts.append(main_acc)

    chunks_with_sub_accounts = split_by_chunks(sub_accounts, settings.PROCESS_COUNT)
    with Pool(settings.PROCESS_COUNT) as p:
        p.map(send_reports_to_main_account, chunks_with_sub_accounts)

    chunks_with_main_accounts = split_by_chunks(main_accounts, settings.PROCESS_COUNT)
    with Pool(settings.PROCESS_COUNT) as p:
        p.map(send_reports_to_chat_bot, chunks_with_main_accounts)

    print(datetime.datetime.now())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
