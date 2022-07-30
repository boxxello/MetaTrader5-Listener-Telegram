import sys


from telethon import TelegramClient, events

from logger import get_logger




class Telegram_c:
    def __init__(self, channel_name, api_id, api_hash, session_name="test"):
        self.logger = get_logger(name="Telegram", name_file='Telegram', time_utc=True)
        self.client = self.start_client(session_name, api_id, api_hash)
        self.channel_name = channel_name

        self.channel_id = self.get_chat_id(channel_name)



    def start_client(self, session_name, api_id, api_hash):
        client = TelegramClient(session_name, api_id, api_hash)
        client.start()
        return client

    def get_chat_id(self, chat_name):
        channel = None
        for dialog in self.client.iter_dialogs():
            if all([x in dialog.name for x in self.channel_name.split(" ")]):
                channel = dialog
                channel_id = dialog.id
                self.logger.info(f"{chat_name} chat found.")
                return channel_id
        self.logger.warning(f"{chat_name} chat not found.")
        sys.exit()
