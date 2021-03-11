import tweepy

from exchange import Coin
from twitter import Twitter
from config import Config
import logger

class App:
	@staticmethod
	def run():
		config = Config.load_config()
		elon_musk_twitter_id = config['twitter']['twitter id']
		price_update_period = config['binance']['period']
		
		Coin().update_price_periodical(price_update_period)
		
		while True:
			try:
				logger.logger.info('connect to '+elon_musk_twitter_id+'...')
				
				streaming_api = tweepy.streaming.Stream(Twitter().oauth1a, Twitter.CustomStreamListener(), timeout=60)
				streaming_api.filter(follow=[elon_musk_twitter_id])
				
			except tweepy.TweepError as e:
				logger.logger.error(e)
				
				continue
				
			except Exception as e:
				logger.logger.error(e)
				
				continue