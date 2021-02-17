import tweepy
import constants
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
					text = status.extended_tweet['full_text'] if status.truncated else status.text
					
					# Don't care about retweets.
					if Twitter.is_rt(text):
						logger.logger.info('retweet.')
						
						return
					
					text_bundle = [text]
					
					if (status.in_reply_to_status_id is None) or (status.in_reply_to_user_id_str == constants.ELON_MUSK_TWITTER_ID):
						text_bundle += Twitter.extract_poll_choices(status)
						
						Twitter.bet_on_tweet(status.user.screen_name, status.created_at, text_bundle, 0.9, 12)
					else:
						Twitter.bet_on_reply(status.user.screen_name, status.created_at, text_bundle, 0.6, 6)
						
			except Exception as e:
				logger.logger.error('Encountered on_status error')
				logger.logger.error(e)
				
		def on_error(self, status_code):
			logger.logger.error('Encountered on_error error with status code:')
			logger.logger.error(status_code)
			
			return True # Don't kill the stream
		
		def on_timeout(self):
			logger.logger.error('Timeout...')
			
			return True # Don't kill the stream
	
	@classmethod
	def extract_poll_choices(cls, status):
		response = subprocess.run(['curl',
								   '--request',
								   'GET',
								   cls.TWITTER_POLL_REQUEST_URL.format(status.id),
								   '--header',
								   'Authorization: Bearer {}'.format(Config.load_config()['twitter']['bearer token'])],
								  capture_output=True)
		
		poll_choices = []
		poll_object = json.loads(response.stdout)
		
		if 'attachments' in poll_object['data'][0]:
			if 'poll_ids' in poll_object['data'][0]['attachments']:
				options = poll_object['includes']['polls'][0]['options']
				for option in options:
					poll_choices.append(option['label'])
		
		return poll_choices
	
	@staticmethod
	def is_rt(text):
		return text.lower().startswith("rt @")
		
	@staticmethod
	def bet_on_tweet(name, datetime, text_bundle, balance_ratio_limit, leverage_limit):
		HIGH_BALANCE_FACTOR = 1.0
		LOW_BALANCE_FACTOR = 0.6
		
		HIGH_LEVERAGE_FACTOR = 1.0
		LOW_LEVERAGE_FACTOR = 0.5
		
		doge_flag = False
		btc_flag = False
		
		for text in text_bundle:
			if text is not None:
				text = text.lower()
				
				if any(x.lower() in text for x in constants.DOGE_KEYWORDS) or any(re.search(x, text, re.IGNORECASE) for x in constants.DOGE_REGEX):
					doge_flag = True
				elif any(x.lower() in text for x in constants.BTC_KEYWORDS):
					btc_flag = True
					
		if doge_flag:
			balance_ratio = balance_ratio_limit * HIGH_BALANCE_FACTOR
			leverage = leverage_limit * HIGH_LEVERAGE_FACTOR
			
			coin_thread = CoinThread(constants.DOGE_SYMBOL, balance_ratio, leverage, 120, True)
			coin_thread.start()
			
			logger.logger.info('doge keywords called.')
			
		elif btc_flag:
			balance_ratio = balance_ratio_limit * HIGH_BALANCE_FACTOR
			leverage = leverage_limit * LOW_LEVERAGE_FACTOR
			
			coin_thread = CoinThread(constants.BTC_SYMBOL, balance_ratio, leverage, 120, True)
			coin_thread.start()
			
			logger.logger.info('btc keywords called.')
			
		else:
			balance_ratio = balance_ratio_limit * LOW_BALANCE_FACTOR
			leverage = leverage_limit * LOW_LEVERAGE_FACTOR
			
			coin_thread = CoinThread(constants.DOGE_SYMBOL, balance_ratio, leverage, 120, False)
			coin_thread.start()
			
			logger.logger.info('neutral tweet.')
			
		text_bundle_message = Telegram.args_to_message(text_bundle)
		message = Telegram.organize_message(name, datetime, text_bundle_message)
		
		Telegram.send_message(Telegram.fetch_chat_id(), message)
		
	@staticmethod
	def bet_on_reply(name, datetime, text_bundle, balance_ratio_limit, leverage_limit):
		HIGH_BALANCE_FACTOR = 1.0
		LOW_BALANCE_FACTOR = 0.6
		
		HIGH_LEVERAGE_FACTOR = 1.0
		LOW_LEVERAGE_FACTOR = 0.5
		
		doge_flag = False
		btc_flag = False
		
		for text in text_bundle:
			if text is not None:
				text = text.lower()
				
				if any(x.lower() in text for x in constants.DOGE_KEYWORDS) or any(re.search(x, text, re.IGNORECASE) for x in constants.DOGE_REGEX):
					doge_flag = True
				elif any(x.lower() in text for x in constants.BTC_KEYWORDS):
					btc_flag = True
		
		if doge_flag:
			balance_ratio = balance_ratio_limit * HIGH_BALANCE_FACTOR
			leverage = leverage_limit * HIGH_LEVERAGE_FACTOR
			
			coin_thread = CoinThread(constants.DOGE_SYMBOL, balance_ratio, leverage, 120, True)
			coin_thread.start()
			
			logger.logger.info('doge keywords called.')
		
		elif btc_flag:
			balance_ratio = balance_ratio_limit * HIGH_BALANCE_FACTOR
			leverage = leverage_limit * LOW_LEVERAGE_FACTOR
			
			coin_thread = CoinThread(constants.BTC_SYMBOL, balance_ratio, leverage, 120, True)
			coin_thread.start()
			
			logger.logger.info('btc keywords called.')
		
		text_bundle_message = Telegram.args_to_message(text_bundle)
		message = Telegram.organize_message(name, datetime, text_bundle_message)
		
		Telegram.send_message(Telegram.fetch_chat_id(), message)