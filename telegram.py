import requests

from config import Config

class Telegram:
	TELEGRAM_GET_UPDATES_BASE_URL = 'https://api.telegram.org/bot{}/getUpdates'
	TELEGRAM_SEND_MESSAGE_BASE_URL = 'https://api.telegram.org/bot{}/sendMessage'
	
	LINE_BREAK = chr(10)
	
	@staticmethod
	def fetch_chat_id():
		return Config.load_config()['telegram']['id']
	
	@classmethod
	def send_message(cls, chat_id, message):
		token = Config.load_config()['telegram']['token']
		send_message_url = cls.TELEGRAM_SEND_MESSAGE_BASE_URL.format(token)
		
		requests.get(send_message_url, params={'chat_id': chat_id, 'text': message, 'parse_mode': 'html'})

	@classmethod
	def organize_message(cls, writer, datetime, text):
		return writer + cls.LINE_BREAK + datetime.isoformat() + cls.LINE_BREAK + text
	
	@classmethod
	def args_to_message(cls, args):
		message = ''
		
		for arg in args:
			message = message + cls.LINE_BREAK + str(arg)
		
		return message