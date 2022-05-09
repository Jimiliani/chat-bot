from accounts_parser import AccountsParser
from settings import ACCOUNT_FILENAME
from tg_account import TelegramAccount


def main():
    parser = AccountsParser(ACCOUNT_FILENAME)
    for acc_data in parser.main_accounts:
        main_acc = TelegramAccount(acc_data)
        for sub_account_data in parser.sub_accounts_by_main_acc(acc_data):
            sub_account = TelegramAccount(sub_account_data)
            sub_account.send_report_to_main_account()
        sub_accounts_usernames = list(map(
            lambda sub_account: sub_account['username'],
            parser.sub_accounts_by_main_acc(acc_data)
        ))
        main_acc.send_reports_to_chat_bot(sub_accounts_usernames)


if __name__ == '__main__':
    main()
