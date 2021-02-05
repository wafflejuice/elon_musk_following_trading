import constants

class Coin:
	@staticmethod
	def get_binance_coin_usdt_id(coin_symbol):
		if coin_symbol == constants.DOGE_SYMBOL:
			return constants.DOGE_SLASH_USDT
		elif coin_symbol == constants.BTC_SYMBOL:
			return constants.BTC_SLASH_USDT
		
	@staticmethod
	def get_futures_coin_usdt_id(coin_symbol):
		if coin_symbol == constants.DOGE_SYMBOL:
			return constants.DOGE_USDT
		elif coin_symbol == constants.BTC_SYMBOL:
			return constants.BTC_USDT