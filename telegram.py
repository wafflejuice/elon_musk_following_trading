import requests

from config import Config

class Telegram:
	TELEGRAM_GET_UPDATES_BASE_URL = 'https://api.telegram.org/bot{}/getUpdates'
	TELEGRAM_SEND_MESSAGE_BASE_URL = 'https://api.telegram.org/bot{}/sendMessage'
	
	# TODO: make the bot handles multiple users
	# TODO: sometimes can't fetch id... So temporarily hard coded chat id.
	@staticmethod
	def fetch_chat_id():
		'''token = Config.load_config()['telegram']['token']
		get_updates_url = constants.TELEGRAM_GET_UPDATES_BASE_URL.format(token)
		
		return json.loads(requests.get(get_updates_url).text)['result'][-1]['message']['from']['id']'''
	
		return Config.load_config()['telegram']['id']
	
	@classmethod
	def send_message(cls, chat_id, message):
		token = Config.load_config()['telegram']['token']
		send_message_url = cls.TELEGRAM_SEND_MESSAGE_BASE_URL.format(token)
		
		requests.get(send_message_url, params={'chat_id': chat_id, 'text': message, 'parse_mode': 'html'})

	@staticmethod
	def organize_message(writer, datetime, text):
		return writer + chr(10) + datetime.isoformat() + chr(10) + text