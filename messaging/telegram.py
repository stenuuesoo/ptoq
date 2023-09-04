import requests


class Telegram:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&text={message}"
        response = requests.get(url)
        return response.json()