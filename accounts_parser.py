import csv
from functools import cached_property
from typing import Dict


class AccountsParser:
    def __init__(self, filename: str):
        if not filename.endswith('.csv'):
            filename += '.csv'
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            self.accounts_rows = list(reader)

    @cached_property
    def main_accounts(self):
        return list(filter(lambda row: row['is_main'] == 'TRUE', self.accounts_rows))

    def sub_accounts_by_main_acc(self, main_acc_row: Dict):
        return list(filter(lambda row: row['send_to'] == main_acc_row['username'], self.accounts_rows))
