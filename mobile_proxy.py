import datetime
import time

import requests

import settings


class MobileProxy:
    user_agent = 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us)'

    def __init__(self, id_, host, port, login, password, key, token):
        self._id = id_
        self._key = key
        self._token = token

        self.ip = self.get_ip()
        self.username = None
        self.host = host
        self.port = port
        self._used_ips = {}
        self._login = login
        self._password = password

    def _as_dict(self):
        return {
            'proxy_type': settings.PROXY_TYPE,
            'addr': self.host,
            'port': self.port,
            'username': self._login,
            'password': self._password,
            'rdns': settings.PROXY_RDNS,
        }

    def as_dict(self, username=None):
        self.username = str(username)
        print(f'[{self.username}][{self._id}]Пытаемся использовать прокси')
        while self._used_ips.get(self.ip, datetime.datetime.min) + datetime.timedelta(minutes=10) > datetime.datetime.now():
            seconds = (datetime.datetime.now() - self._used_ips[self.ip]).seconds
            print(f'[{self.username}][{self._id}]IP {self.ip} был использован {seconds // 60} минут {seconds % 60} секунд назад')
            print(self._used_ips.get(self.ip, datetime.datetime.min))
            print(datetime.datetime.now())
            self.change_ip()
        self._update_used_ip()
        print(f'[{self.username}][{self._id}]Используем прокси с IP {self.ip}')
        self.username = None
        return self._as_dict()

    def _update_used_ip(self):
        self._used_ips[self.ip] = datetime.datetime.now()

    def _send_request(self, method: str):
        response = requests.get(
            method.format(proxy_id=self._id, proxy_key=self._key),
            headers={
                'Authorization': f'Bearer {self._token}',
                'User-Agent': self.user_agent,
            },
        )
        print(f'[{self.username}][{self._id}]{response.json()}')
        return response

    def change_equipment(self):
        while True:
            print(f'[{self.username}][{self._id}]Получаем новое оборудование')
            response = self._send_request(settings.ProxyMethods.CHANGE_EQUIPMENT)
            if 'message' in response.json()['status']:
                self._update_used_ip()
                self.ip = self.get_ip()
            else:
                print(f'[{self.username}][{self._id}]С прошлой смены оборудования прошло меньше 10 минут, ждем 1 минуту')
                time.sleep(60)

    def change_ip(self):
        retries = 3
        while True:
            print(f'[{self.username}][{self._id}]Получаем новый IP')
            response = self._send_request(settings.ProxyMethods.CHANGE_IP)
            new_ip = response.json().get('new_ip', None)
            if new_ip is None:
                print(f'[{self.username}][{self._id}]Плохой ответ, повторяем запрос')
                continue
            if new_ip != self.ip:
                print(f'[{self.username}][{self._id}]Новый IP - {new_ip}')
                self.ip = new_ip
                break
            elif retries == 0:
                self.change_equipment()
                break
            else:
                retries -= 1
            print(f'[{self.username}][{self._id}]Новый IP совпадает со старым, повторяем запрос')

    def get_ip(self):
        while True:
            print(f'[{self.username}][{self._id}]Получаем текущий IP')
            response = self._send_request(settings.ProxyMethods.GET_IP)
            if response.json().get('proxy_id') is not None:
                ip = response.json()['proxy_id'].get(str(self._id))
                if ip:
                    print(f'[{self.username}][{self._id}]Текущий IP - {ip}')
                    return ip
            print(f'[{self.username}][{self._id}]Полученный IP - невалидный, повторяем запрос')
