import csv
import os
from functools import cached_property
from typing import Dict, Optional

import settings
import utils


class AccountsParser:
    def __init__(self, accounts_filename: str, img_dir_filename: str, links_filename: str):
        accounts_filename = self._fix_filename(accounts_filename)
        links_filename = self._fix_filename(links_filename)

        self._check_existence(accounts_filename)
        self._check_existence(img_dir_filename)
        self._check_existence(links_filename)

        with open(accounts_filename, mode='r') as file:
            reader = csv.DictReader(file)
            accounts_rows = list(reader)
        with open(links_filename, mode='r') as file:
            reader = csv.DictReader(file)
            links_rows = list(reader)
            self.links_required = len(links_rows) > 0
        images_paths = list(
            filter(
                lambda filename: filename.split('.')[-1] in settings.ALLOWED_IMAGES_EXTENSIONS,
                os.listdir(img_dir_filename)
            )
        )
        self._assemble_account_data(accounts_rows, images_paths, links_rows)

    def _assemble_account_data(self, accounts_rows, images_paths, links_rows):
        if 0 < len(links_rows) != len(images_paths):
            raise AssertionError(
                f'Количество ссылок({len(links_rows)}) не совпадает с количеством изображений({len(images_paths)}).\n'
                f'Обратите внимание на доступные расширения изображений: {settings.ALLOWED_IMAGES_EXTENSIONS}'
            )
        if len(accounts_rows) != len(images_paths):
            raise AssertionError(
                f'Количество аккаунтов({len(accounts_rows)}) не совпадает '
                f'с количеством изображений({len(images_paths)})'
            )
        accounts_data = []
        iteration = 1
        for account in accounts_rows:
            accounts_data.append({
                **account,
                'image_path': self._get_path_to_image_with_name(images_paths, iteration),
                'link': self._get_link_with_number(links_rows, iteration),
            })
            iteration += 1
        self.accounts_data = accounts_data
        if len(self.accounts_data) > len(utils.get_proxies()) * settings.ACCOUNTS_ON_PROXY:
            raise RuntimeError(
                f'Количество проксей[{len(settings.PROXY_ADDR_LIST)}] '
                f'* Количество аккаунтов на 1 прокси[{settings.ACCOUNTS_ON_PROXY}] '
                f'< Количество аккаунтов[{len(accounts_data)}]'
            )

    @staticmethod
    def _get_path_to_image_with_name(images_paths, number) -> str:
        try:
            return next(
                filter(
                    lambda path: int(path.split('.')[0]) == number, images_paths
                )
            )
        except StopIteration:
            raise AssertionError(f'Не найдена картинка с номером {number}')

    def _get_link_with_number(self, links_rows, number) -> Optional[str]:
        if not self.links_required:
            return None
        try:
            return links_rows[number - 1]['links']
        except IndexError:
            raise AssertionError(f'Не найдена ссылка в строке {number + 1}')

    @staticmethod
    def _fix_filename(filename: str):
        if not filename.endswith('.csv'):
            filename += '.csv'
        return filename

    @staticmethod
    def _check_existence(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f'Файл/папка {path} не существует')

    @cached_property
    def main_accounts(self):
        return list(filter(lambda row: row['is_main'] == 'TRUE', self.accounts_data))

    def sub_accounts_by_main_acc(self, main_acc_row: Dict):
        return list(filter(lambda row: row['send_to'] == main_acc_row['username'], self.accounts_data))
