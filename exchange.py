import ccxt
import time
import multiprocessing

from config import Config
import constants
import logger


class Futures:
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, "_instance"):
			cls._instance = super().__new__(cls)
		return cls._instance
	
	def __init__(self):
		cls = type(self)
		if not hasattr(cls, "_init"):
			self.futures = self.get_futures()
			
			cls._init = True
			
	@staticmethod
	def get_futures():
		config = Config.load_config()
		futures = ccxt.binance({
			'apiKey': config['binance']['api_key'],
			'secret': config['binance']['secret_key'],
			'enableRateLimit': True,
			'options': {
				'defaultType': 'future',
			},
		})
		
		return futures
	
	def fetch_futures_usdt_balance(self):
		futures_balance = self.futures.fapiPrivateGetBalance()
		futures_balance_chunk = list(filter(lambda x: x['asset'] == constants.USDT_SYMBOL, futures_balance))[0]
		futures_usdt_balance = float(futures_balance_chunk['balance'])
		
		return futures_usdt_balance
	
	def fetch_futures_coin_position(self, coin_symbol):
		futures_positions = self.futures.fetch_positions()
		futures_coin_positions = list(filter(lambda x: x['symbol'] == Coin.get_futures_coin_usdt_id(coin_symbol), futures_positions))
		futures_coin_position = float(futures_coin_positions[0]['positionAmt'])
		
		return futures_coin_position

	def fetch_futures_coin_price_usdt(self, coin_symbol):
		futures_coin_ticker = self.futures.fapiPublicGetTickerPrice({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol)
		})
		futures_coin_price = float(futures_coin_ticker['price'])
		
		return futures_coin_price

	def adjust_futures_leverage(self, coin_symbol, leverage):
		if leverage < 1:
			raise ValueError("leverage should be at least x1")
		
		self.futures.fapiPrivatePostLeverage({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'leverage': leverage,
		})
	
	def futures_market_order(self, coin_symbol, coin_count, side, reduce_only):
		res = None
		if reduce_only:
			res = self.futures.fapiPrivatePostOrder({
				'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
				'side': side,
				'type': 'MARKET',
				'quantity': coin_count,
				'reduceOnly': 'true',
			})
		else:
			res = self.futures.fapiPrivatePostOrder({
				'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
				'side': side,
				'type': 'MARKET',
				'quantity': coin_count,
			})
		
		logger.logger.info(res)

	@staticmethod
	def futures_market_long(coin_symbol, coin_count, reduce_only):
		Futures().futures_market_order(coin_symbol, coin_count, 'BUY', reduce_only)

	@staticmethod
	def futures_market_short(coin_symbol, coin_count, reduce_only):
		Futures().futures_market_order(coin_symbol, coin_count, 'SELL', reduce_only)
			
class Coin:
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, "_instance"):
			cls._instance = super().__new__(cls)
		return cls._instance
	
	def __init__(self):
		cls = type(self)
		if not hasattr(cls, "_init"):
			self.doge_price_store = Futures().fetch_futures_coin_price_usdt(constants.DOGE_SYMBOL)
			
			cls._init = True
	
	def update_price(self):
		self.doge_price_store = Futures().fetch_futures_coin_price_usdt(constants.DOGE_SYMBOL)
		
	def update_price_periodical(self, period):
		update_price_process = multiprocessing.Process(target=self.update_price_periodical_process, args=(period,))
		update_price_process.start()
	
	def update_price_periodical_process(self, period):
		while True:
			try:
				self.update_price()
				time.sleep(period)
				
			except Exception as e:
				logger.logger.error(e)
	
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
	
	def run(self, symbol, balance, duration):
		if symbol == constants.DOGE_SYMBOL:
			coin_count = int(balance / self.doge_price_store)
			
			try:
				Futures().futures_market_long(symbol, coin_count, False)
				
				half_coin_count = int(coin_count * 0.5)
				half_duration = duration * 0.5
				
				time.sleep(half_duration)
				Futures().futures_market_short(symbol, half_coin_count, True)
				
				time.sleep(half_duration)
				Futures().futures_market_short(symbol, coin_count - half_coin_count, True)
				
				self.update_price()
			
			except Exception as e:
				logger.logger.error(e)