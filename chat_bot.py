import settings


class ChatBotDialog:
    def __init__(self, client):
        self.client = client

    def get_dialog(self):
        try:
            return list(
                filter(
                    lambda dialog: dialog.entity.id == settings.CHAT_BOT_TG_ID,
                    self.client.loop.run_until_complete(self.client.get_dialogs())
                )
            )[0]
        except IndexError:
            print(f'Непредвиденная ошибка: не найден диалог с чат ботом')

    def get_last_message(self):
        return self.get_dialog().message

    def get_buttons_from_last_message(self):
        return [
            button
            for buttons_group in self.get_last_message().buttons
            for button in buttons_group
        ]

    def get_buttons_texts(self):
        return '\n'.join(
            map(
                lambda btn: btn.text,
                self.get_buttons_from_last_message()
            )
        )

    def get_button_with_text(self, text):
        try:
            return list(
                filter(
                    lambda btn: btn.message == text, self.get_buttons_from_last_message()
                )
            )[0]
        except IndexError:
            print(f'Непредвиденная ошибка: не найдена кнопка с текстом {text}')
