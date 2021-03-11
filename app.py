import tweepy

from exchange import Coin
from twitter import Twitter
from config import Config
import logger
import constants

class App:
	@staticmethod
	def run():
		config = Config.load_config()
		price_update_period = config['binance']['period']
		
		Coin().update_price_periodical(price_update_period)
		
		while True:
			try:
				logger.logger.info('connect to '+constants.ELON_MUSK_TWITTER_ID+'...')
				
				streaming_api = tweepy.streaming.Stream(Twitter().oauth1a, Twitter.CustomStreamListener(), timeout=60)
				streaming_api.filter(follow=[constants.ELON_MUSK_TWITTER_ID])
				
			except tweepy.TweepError as e:
				logger.logger.error(e)
				
				continue
				
			except Exception as e:
				logger.logger.error(e)
				
				continue