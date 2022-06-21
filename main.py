import asyncio
import datetime
from multiprocessing import Pool

import utils
from accounts_parser import AccountsParser
from tg_account import B0TelegramAccount, B1TelegramAccount

import settings
from utils import split_by_chunks, send_reports_to_main_account, send_reports_to_chat_bot, set_completed


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
    counter = 0
    proxies = utils.get_proxies()
    for acc_data in parser.main_accounts:
        counter += 1
        print(acc_data)
        current_acc_sub_accounts = []
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            counter += 1
            print(sub_account_data)
            sub_account = B0TelegramAccount(sub_account_data, proxies[counter % len(proxies)])
            current_acc_sub_accounts.append(sub_account)
            sub_accounts.append(sub_account)
        main_accounts.append(B1TelegramAccount(acc_data, proxies[counter % len(proxies)], current_acc_sub_accounts))

    result = []
    errors = []
    chunks_with_sub_accounts = list(split_by_chunks(sub_accounts, settings.PROCESS_COUNT))
    with Pool(settings.PROCESS_COUNT) as p:
        result.extend(p.map(send_reports_to_main_account, chunks_with_sub_accounts))

    for usernames_list in result:
        for username in usernames_list:
            is_username = set_completed(username, sub_accounts)
            if not is_username:
                errors.append(username)

    errors_lists = [errors]
    chunks_with_main_accounts = split_by_chunks(main_accounts, settings.PROCESS_COUNT)
    with Pool(settings.PROCESS_COUNT) as p:
        errors_lists.extend(p.map(send_reports_to_chat_bot, chunks_with_main_accounts))

    for error in [error for errors_list in errors_lists for error in errors_list]:
        print(error)
    print(datetime.datetime.now())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
