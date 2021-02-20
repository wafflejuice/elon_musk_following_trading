import tweepy

from twitter import Twitter
import constants
import logger

def run():
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