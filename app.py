import tweepy

from config import Config
from twitter import Twitter
import constants
import logger

def run():
	config = Config.load_config()
	
	while True:
		try:
			logger.logger.info('connect to '+constants.ELON_MUSK_TWITTER_ID+'...')
			
			auth = tweepy.OAuthHandler(config['twitter']['api key'], config['twitter']['api secret key'])
			auth.set_access_token(config['twitter']['access token'], config['twitter']['access token secret'])
			
			streaming_api = tweepy.streaming.Stream(auth, Twitter.CustomStreamListener(), timeout=60)
			streaming_api.filter(follow=[constants.ELON_MUSK_TWITTER_ID])
		except tweepy.TweepError as e:
			logger.logger.error(e)
			
			continue
		except Exception as e:
			logger.logger.error(e)
			
			continue