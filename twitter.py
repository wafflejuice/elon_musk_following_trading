import tweepy
import constants
import subprocess
import json
import re
import time

from exchange import Futures
from exchange import Coin
from telegram import Telegram
from config import Config
import logger


class Twitter:
	TWITTER_POLL_REQUEST_URL = 'https://api.twitter.com/2/tweets?ids={}&expansions=attachments.poll_ids&poll.fields=duration_minutes,end_datetime,id,options,voting_status'
	
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, "_instance"):
			cls._instance = super().__new__(cls)
		return cls._instance
	
	def __init__(self):
		cls = type(self)
		if not hasattr(cls, "_init"):
			cls._init = True
			
			config = Config.load_config()
			self.oauth1a = tweepy.OAuthHandler(config['twitter']['api key'], config['twitter']['api secret key'])
			self.oauth1a.set_access_token(config['twitter']['access token'], config['twitter']['access token secret'])
			self.api = tweepy.API(Twitter().oauth1a)
	
	class CustomStreamListener(tweepy.StreamListener):
		def on_status(self, status):
			try:
				if status.user.id_str == constants.ELON_MUSK_TWITTER_ID and Twitter.is_thread_monopoly(status):
					text = status.extended_tweet['full_text'] if status.truncated else status.text
	
					# Don't care about retweets.
					if Twitter.is_rt(text):
						return
					
					text_bundle = [text]
					#text_bundle += Twitter.extract_poll_choices(status)
					
					Twitter.bet_on_tweet_steady(status.user.screen_name, status.created_at, text_bundle, 7200)
		
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

	@staticmethod
	def is_rt(text):
		return text.lower().startswith("rt @")
	
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
	
	@classmethod
	def find_thread_start_user_id_str(cls, status):
		if status.in_reply_to_status_id is None:
			return status.user.id_str
		
		api = tweepy.API(Twitter().oauth1a)
		target_status = api.get_status(status.in_reply_to_status_id)
		
		return cls.find_thread_start_user_id_str(target_status)

	@classmethod
	def is_thread_monopoly(cls, status):
		if status.in_reply_to_status_id is None:
			return True
		
		if status.in_reply_to_user_id_str != status.user.id_str:
			return False
		
		target_status = Twitter().api.get_status(status.in_reply_to_status_id)
		
		return cls.is_thread_monopoly(target_status)
	
	@staticmethod
	def bet_on_tweet_steady(name, datetime, text_bundle, balance):
		doge_flag = False
		
		for text in text_bundle:
			if text is not None:
				text = text.lower()
				
				if any(x.lower() in text for x in constants.DOGE_KEYWORDS) or any(
						re.search(x, text, re.IGNORECASE) for x in constants.DOGE_REGEX):
					doge_flag = True
					
					break
		
		if doge_flag:
			Coin().run(constants.DOGE_SYMBOL, balance, 120)
			
			log_time = time.strftime('%c', time.localtime(time.time()))
			logger.logger.info(log_time)
			logger.logger.info("doge keywords called.")
			
			remaining_balance = Futures().fetch_futures_usdt_balance()
			text_bundle += ["remaining balance is", str(remaining_balance)]
			text_bundle_message = Telegram.args_to_message(text_bundle)
			message = Telegram.organize_message(name, datetime, text_bundle_message)
			
			Telegram.send_message(Telegram.fetch_chat_id(), message)