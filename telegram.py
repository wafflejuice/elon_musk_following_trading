import requests
import json

from config import Config
import constants

class Telegram:
	# TODO: make the bot handles multiple users
	@staticmethod
	def fetch_chat_id():
		token = Config.load_config()['telegram']['token']
		get_updates_url = constants.TELEGRAM_GET_UPDATES_BASE_URL.format(token)
		
		return json.loads(requests.get(get_updates_url).text)['result'][-1]['message']['from']['id']
	
	@staticmethod
	def send_message(chat_id, message):
		token = Config.load_config()['telegram']['token']
		send_message_url = constants.TELEGRAM_SEND_MESSAGE_BASE_URL.format(token)
		
		requests.get(send_message_url, params={'chat_id': chat_id, 'text': message, 'parse_mode': 'html'})

	@staticmethod
	def organize_message(writer, datetime, text):
		return writer + chr(10) + datetime.isoformat() + chr(10) + text