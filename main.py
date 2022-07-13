import asyncio
import datetime
import functools
import sys
from multiprocessing import Pool

import utils
from accounts_parser import AccountsParser
from tg_account import B0TelegramAccount, B1TelegramAccount

import settings
from utils import split_by_chunks, send_reports_to_main_account, send_reports_to_chat_bot, set_completed


async def main(skip_b0):
    print('Введите название задачи(или его часть):')
    task_name = str(input())
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
        current_acc_sub_accounts = []
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            counter += 1
            sub_account = B0TelegramAccount(sub_account_data, proxies[counter % len(proxies)])
            sub_account.completed = skip_b0
            current_acc_sub_accounts.append(sub_account)
            sub_accounts.append(sub_account)
        main_accounts.append(B1TelegramAccount(acc_data, proxies[counter % len(proxies)], current_acc_sub_accounts))
    print('Аккаунты нормальные, начинаем отправку отчетов за себя от Б1 в чб')

    result = []
    errors = []
    errors_lists = []

    chunks_with_sub_accounts = list(split_by_chunks(sub_accounts, settings.PROCESS_COUNT))
    chunks_with_main_accounts = split_by_chunks(main_accounts, settings.PROCESS_COUNT)
    with Pool(settings.PROCESS_COUNT) as p:
        errors_lists.extend(
            p.map(
                functools.partial(
                    send_reports_to_chat_bot,
                    task_name=task_name,
                    send_for='b1'
                ),
                chunks_with_main_accounts
            )
        )
    print('Б1 отправили отчеты за себя, начинаем отправку от Б0 к Б1')

    if not skip_b0:
        with Pool(settings.PROCESS_COUNT) as p:
            result.extend(p.map(send_reports_to_main_account, chunks_with_sub_accounts))
    print('Б0 отправили отчеты к своим Б1, начинаем отправку от Б1 в чб за команду')

    for usernames_list in result:
        for username in usernames_list:
            completed = set_completed(username, sub_accounts)
            if not completed:
                errors.append(username)
    errors_lists.append(errors)

    with Pool(settings.PROCESS_COUNT) as p:
        errors_lists.extend(
            p.map(
                functools.partial(
                    send_reports_to_chat_bot,
                    task_name=task_name,
                    send_for='b0'
                ),
                chunks_with_main_accounts
            )
        )
    print('Б1 отправили отчеты  за команду')
    settings.logging.info(f'Отчеты отправлены, ошибки возникшие в ходе работы программы:\n {errors_lists}')

    print('Отчеты отправлены, ошибки возникшие в ходе работы программы:')
    for error in [error for errors_list in errors_lists for error in errors_list]:
        print(error)
    print(datetime.datetime.now())


if __name__ == '__main__':
    print(sys.argv)
    skip_b0 = False
    if '--skip-b0' in sys.argv:
        skip_b0 = True
    print(skip_b0)
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(skip_b0))
