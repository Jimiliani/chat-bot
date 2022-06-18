import asyncio
import datetime
from multiprocessing import Pool

import utils
from accounts_parser import AccountsParser
from tg_account import B0TelegramAccount, B1TelegramAccount

import settings
from utils import split_by_chunks, send_reports_to_main_account, send_reports_to_chat_bot


async def main():
    print('Введите название задачи(или его часть):')
    settings.TASK_NAME = str(input())
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
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            sub_accounts.append(B0TelegramAccount(sub_account_data, next(proxies)))
        main_accounts.append(B1TelegramAccount(acc_data, next(proxies), sub_accounts))

    errors_lists = []
    chunks_with_sub_accounts = split_by_chunks(sub_accounts, settings.PROCESS_COUNT)
    with Pool(settings.PROCESS_COUNT) as p:
        errors_lists.extend(p.map(send_reports_to_main_account, chunks_with_sub_accounts))

    chunks_with_main_accounts = split_by_chunks(main_accounts, settings.PROCESS_COUNT)
    with Pool(settings.PROCESS_COUNT) as p:
        errors_lists.extend(p.map(send_reports_to_chat_bot, chunks_with_main_accounts))
    for error in [error for errors_list in errors_lists for error in errors_list]:
        print(error)
    print(datetime.datetime.now())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
