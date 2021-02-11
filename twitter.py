import tweepy
import constants
import sys
import subprocess
import json
import re

from exchange import CoinThread
from telegram import Telegram
from config import Config
import logger

class Twitter:
	TWITTER_POLL_REQUEST_URL = 'https://api.twitter.com/2/tweets?ids={}&expansions=attachments.poll_ids&poll.fields=duration_minutes,end_datetime,id,options,voting_status'
	
	class CustomStreamListener(tweepy.StreamListener):
		def on_status(self, status):
			try:
				if status.user.id_str == constants.ELON_MUSK_TWITTER_ID:
					if (status.in_reply_to_status_id is None) or (status.in_reply_to_user_id_str == constants.ELON_MUSK_TWITTER_ID):
						text = status.extended_tweet['full_text'] if status.truncated else status.text
						
						# handle poll
						# TODO: os specific
						response = subprocess.run(['curl',
												   '--request',
												   'GET',
												   Twitter.TWITTER_POLL_REQUEST_URL.format(status.id),
												   '--header',
												   'Authorization: Bearer {}'.format(Config.load_config()['twitter']['bearer token'])],
												  capture_output=True)

						poll_label_mixture_text = ''
						poll_object = json.loads(response.stdout)
						
						if 'attachments' in poll_object['data'][0]:
							if 'poll_ids' in poll_object['data'][0]['attachments']:
								options = poll_object['includes']['polls'][0]['options']
								for option in options:
									poll_label_mixture_text += option['label']
						
						text += poll_label_mixture_text
						Twitter.handle_tweet(status.user.screen_name, status.created_at, text)
			except Exception as e:
				logger.logger.error(e)
				
		def on_error(self, status_code):
			logger.logger.error('Encountered error with status code:')
			logger.logger.error(status_code)
			
			return True # Don't kill the stream
		
		def on_timeout(self):
			logger.logger.error('Timeout...')
			
			return True # Don't kill the stream
		
	@staticmethod
	def handle_tweet(name, datetime, text):
		if text:
			original_text = text
			lowercase_text = text.lower()
			
			# Don't care about retweets.
			if lowercase_text.startswith("rt @"):
				logger.logger.info('retweet.')
				
				return
			
			if any(x.lower() in lowercase_text for x in constants.DOGE_KEYWORDS) or any(re.search(x, lowercase_text, re.IGNORECASE) for x in constants.DOGE_REGEX):
				logger.logger.info('doge keywords called.')
				
				coin_thread = CoinThread(constants.DOGE_SYMBOL, 0.9, 12, 120, True)
				coin_thread.start()
				
			elif any(x.lower() in lowercase_text for x in constants.BTC_KEYWORDS):
				logger.logger.info('btc keywords called.')
				
				coin_thread = CoinThread(constants.BTC_SYMBOL, 0.9, 5, 120, True)
				coin_thread.start()
			else:
				logger.logger.info('neutral tweet.')
				
				coin_thread = CoinThread(constants.DOGE_SYMBOL, 0.6, 5, 120, False)
				coin_thread.start()
			
			Telegram.send_message(Telegram.fetch_chat_id(), Telegram.organize_message(name, datetime, original_text))