from accounts_parser import AccountsParser
from tg_account import TelegramAccount

import settings


def main():
    parser = AccountsParser(
        settings.ACCOUNTS_FILENAME,
        settings.IMAGES_DIRECTORY_NAME,
        settings.LINKS_FILENAME
    )
    for acc_data in parser.main_accounts:
        main_acc = TelegramAccount(acc_data)
        main_acc_id = main_acc.get_id()
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            sub_account = TelegramAccount(sub_account_data, main_acc_id)
            sub_account.send_report_to_main_account()
        sub_accounts_usernames = list(map(
            lambda sub_account: sub_account['username'],
            parser.sub_accounts_by_main_acc(acc_data)
        ))
        main_acc.send_reports_to_chat_bot(sub_accounts_usernames)


if __name__ == '__main__':
    main()