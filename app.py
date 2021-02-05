import ccxt
import tweepy
import requests
import json
import time
import sys
import threading

import exchange.exchange as exchange
import exchange.transaction as transaction

import database
import twitter
import constants

class Manager(object):
	__has_position = None
	
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, "_instance"):
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self):
		cls = type(self)
		if not hasattr(cls, "_init"):
			self.__has_position = False
			cls._init = True
			
	def get_has_position(self):
		return self.__has_position
	
	def set_has_position(self, has_position):
		self.__has_position = has_position

class CoinThread(threading.Thread):
	__futures = None
	__coin_symbol = None
	__leverage = None
	
	def get_coin_symbol(self):
		return self.__coin_symbol
	def get_leverage(self):
		return self.__leverage
	
	def set_futures(self, futures):
		self.__futures = futures
	def set_coin_symbol(self, coin_symbol):
		self.__coin_symbol = coin_symbol
	def set_leverage(self, leverage):
		self.__leverage = leverage
	
	def run(self):
		Manager().set_has_position(True)
		
		round_digit = None
		
		if self.__coin_symbol == constants.DOGE_SYMBOL:
			round_digit = 0
		elif self.__coin_symbol == constants.BTC_SYMBOL:
			round_digit = 3
			
		exchange.adjust_futures_leverage(self.__futures, self.__coin_symbol, self.__leverage)
		coin_count = round(0.9 * float(self.__leverage) * exchange.fetch_futures_usdt_balance(self.__futures) / exchange.fetch_futures_coin_price_usdt(self.__futures, self.__coin_symbol), round_digit)
		transaction.futures_market_long(self.__futures, self.__coin_symbol, coin_count, False)

		time.sleep(constants.HOUR_S * 0.5)

		transaction.futures_market_short(self.__futures, self.__coin_symbol, coin_count, True)
		
		Manager().set_has_position(False)


def run():
	file = open('config_mine.json', 'r')
	info = json.loads(file.read())
	file.close()
	
	futures = ccxt.binance({
		'apiKey': info['binance']['api_key'],
		'secret': info['binance']['secret_key'],
		'enableRateLimit': True,
		'options': {
			'defaultType': 'future',
		},
	})

	database.Database().connect(info['mariaDB']['host'], info['mariaDB']['port'], info['mariaDB']['user'], info['mariaDB']['passwd'])
	
	database.Database().execute("CREATE DATABASE IF NOT EXISTS elon_musk_twitter")
	database.Database().execute("USE elon_musk_twitter")
	database.Database().execute("CREATE TABLE IF NOT EXISTS elon_musk_tweet(id VARCHAR(20) PRIMARY KEY, text TEXT)")
	database.Database().execute("ALTER TABLE elon_musk_tweet CONVERT TO CHARSET UTF8")
	
	database.Database().commit()
	
	telegram_get_updates_url = constants.TELEGRAM_GET_UPDATES_BASE_URL.format(info['telegram']['token'])
	telegram_send_message_url = constants.TELEGRAM_SEND_MESSAGE_BASE_URL.format(info['telegram']['token'])
	
	# TODO: make the bot handles multiple users
	chat_id = json.loads(requests.get(telegram_get_updates_url).text)['result'][-1]['message']['from']['id']
	
	def handle_text(name, datetime, text):
		if text:
			original_text = text
			lowercase_text = text.lower()
			
			# Don't care about retweets.
			if lowercase_text.startswith("rt @"):
				print('This is retweet')
				return
			
			if any(x in lowercase_text for x in constants.TOTAL_KEYWORDS):
				requests.get(telegram_send_message_url, params={'chat_id': chat_id, 'text': text_to_message(name, datetime, original_text), 'parse_mode': 'html'})
				
			if any(x in lowercase_text for x in constants.DOGE_KEYWORDS):
				print('doge case')
				
				if not Manager().get_has_position():
					thread = CoinThread()
					thread.set_futures(futures)
					thread.set_coin_symbol(constants.DOGE_SYMBOL)
					thread.set_leverage(5)
					thread.start()
			elif any(x in lowercase_text for x in constants.BTC_KEYWORDS):
				print('btc case')
				
				if not Manager().get_has_position():
					thread = CoinThread()
					thread.set_futures(futures)
					thread.set_coin_symbol(constants.BTC_SYMBOL)
					thread.set_leverage(5)
					thread.start()
				
	def text_to_message(writer, datetime, text):
		return writer + chr(10) + datetime.isoformat() + chr(10) + text
	
	class CustomStreamListener(tweepy.StreamListener):
		def on_status(self, status):
			try:
				text = None
				if status.user.id_str == constants.ELON_MUSK_TWITTER_ID:
					if status.in_reply_to_status_id is None:
						if status.truncated:
							text = status.extended_tweet['full_text']
						else:
							text = status.text
					else:
						if status.in_reply_to_user_id_str == constants.ELON_MUSK_TWITTER_ID:
							if status.truncated:
								text = status.extended_tweet['full_text']
							else:
								text = status.text
				
				handle_text(status.user.screen_name, status.created_at, text)
			except Exception as e:
				print('on_status: error occurred: '+str(e))
			
		def on_error(self, status_code):
			print(sys.stderr, 'Encountered error with status code:', status_code)
			return True  # Don't kill the stream
		
		def on_timeout(self):
			print('timeout timeout timeout')
			print(sys.stderr, 'Timeout...')
			return True  # Don't kill the stream
	
	
	auth = tweepy.OAuthHandler(info['twitter']['api key'], info['twitter']['api secret key'])
	auth.set_access_token(info['twitter']['access token'], info['twitter']['access token secret'])
		
	# TODO: make a new thread handle this.
	streaming_api = tweepy.streaming.Stream(auth, CustomStreamListener(), timeout=60)
	streaming_api.filter(follow=[constants.ELON_MUSK_TWITTER_ID])