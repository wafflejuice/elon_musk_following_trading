import tweepy
import constants
import sys

from exchange import Manager
from exchange import CoinThread
from telegram import Telegram

class Twitter:
	class CustomStreamListener(tweepy.StreamListener):
		def on_status(self, status):
			'''print(status.user.screen_name)
			print(status.created_at)
			print(status.extended_tweet['full_text'] if status.truncated else status.text)
			print()'''
			
			try:
				if status.user.id_str == constants.ELON_MUSK_TWITTER_ID:
					if (status.in_reply_to_status_id is None) or (status.in_reply_to_user_id_str == constants.ELON_MUSK_TWITTER_ID):
						text = status.extended_tweet['full_text'] if status.truncated else status.text
						Twitter.handle_tweet(status.user.screen_name, status.created_at, text)
			except:
				print(sys.stderr, 'Encountered status error')
				
		def on_error(self, status_code):
			print(sys.stderr, 'Encountered error with status code:', status_code)
			return True # Don't kill the stream
		
		def on_timeout(self):
			print(sys.stderr, 'Timeout...')
			return True # Don't kill the stream
		
	@staticmethod
	def handle_tweet(name, datetime, text):
		if text:
			original_text = text
			lowercase_text = text.lower()
			
			# Don't care about retweets.
			if lowercase_text.startswith("rt @"):
				print("retweeted.")
				return
			
			if not Manager().get_has_position():
				if any(x.lower() in lowercase_text for x in constants.DOGE_KEYWORDS):
					print('doge keywords called.')
					
					coin_thread = CoinThread(constants.DOGE_SYMBOL, 8)
					coin_thread.start()
					
				elif any(x.lower() in lowercase_text for x in constants.BTC_KEYWORDS):
					print('btc keywords called.')
					
					coin_thread = CoinThread(constants.BTC_SYMBOL, 5)
					coin_thread.start()
			
			total_keywords = constants.DOGE_KEYWORDS + constants.BTC_KEYWORDS + constants.OTHER_KEYWORDS
			
			if any(x in lowercase_text for x in total_keywords):
				Telegram.send_message(Telegram.fetch_chat_id(), Telegram.organize_message(name, datetime, original_text))