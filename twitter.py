import tweepy
import constants

class Twitter(object):
	__auth = None
	__stream_listener = None
	__stream = None
	
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, "_instance"):
			cls._instance = super().__new__(cls)
		return cls._instance
	
	def authentificate(self, twitter_api_key, twitter_api_secret_key, twitter_access_token, twitter_access_token_secret):
		self.__auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret_key)
		self.__auth.set_access_token(twitter_access_token, twitter_access_token_secret)
	
	def get_twitter_stream(self, twitter_ids, keywords):
		__stream = tweepy.Stream(self.__auth, self.MyStreamListener())
		__stream.filter(follow=twitter_ids, track=keywords)
	
	def get_api(self):
		return tweepy.API(self.__auth)
		
	class MyStreamListener(tweepy.StreamListener):
		def on_status(self, status):
			print(status.text)