import ccxt
import threading
import time

from config import Config
import constants
import logger

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

class Binance:
	@staticmethod
	def fetch_binance_usdt_balance(binance):
		return binance.fetch_balance()[constants.USDT_SYMBOL]['free']


class Futures:
	@staticmethod
	def fetch_futures_usdt_balance(futures):
		futures_balance = futures.fapiPrivateGetBalance()
		futures_balance_chunk = list(filter(lambda x: x['asset'] == constants.USDT_SYMBOL, futures_balance))[0]
		futures_usdt_balance = float(futures_balance_chunk['balance'])
		
		return futures_usdt_balance
	
	@staticmethod
	def fetch_futures_coin_position(futures, coin_symbol):
		futures_positions = futures.fetch_positions()
		futures_coin_positions = list(filter(lambda x: x['symbol'] == Coin.get_futures_coin_usdt_id(coin_symbol), futures_positions))
		futures_coin_position = float(futures_coin_positions[0]['positionAmt'])
		
		return futures_coin_position

	@staticmethod
	def fetch_futures_coin_price_usdt(futures, coin_symbol):
		futures_coin_ticker = futures.fapiPublicGetTickerPrice({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol)
		})
		futures_coin_price = float(futures_coin_ticker['price'])
		
		return futures_coin_price

	@staticmethod
	def adjust_futures_leverage(futures, coin_symbol, leverage):
		if leverage < 1:
			raise ValueError("leverage should be at least x1")
		
		futures.fapiPrivatePostLeverage({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'leverage': leverage,
		})
	
	@staticmethod
	def futures_market_order(futures, coin_symbol, coin_count, side, reduce_only):
		if reduce_only:
			futures.fapiPrivatePostOrder({
				'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
				'side': side,
				'type': 'MARKET',
				'quantity': coin_count,
				'reduceOnly': 'true',
			})
		else:
			futures.fapiPrivatePostOrder({
				'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
				'side': side,
				'type': 'MARKET',
				'quantity': coin_count,
			})

	@staticmethod
	def futures_market_long(futures, coin_symbol, coin_count, reduce_only):
		Futures.futures_market_order(futures, coin_symbol, coin_count, 'BUY', reduce_only)
	
	@staticmethod
	def futures_market_short(futures, coin_symbol, coin_count, reduce_only):
		Futures.futures_market_order(futures, coin_symbol, coin_count, 'SELL', reduce_only)
			
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
		
class CoinThread(threading.Thread):
	def __init__(self, coin_symbol, balance_ratio, leverage, duration, is_prime):
		threading.Thread.__init__(self)
		
		self.flag_lock = threading.Lock()
		
		self.__safe_profit_flag = False
		
		self.__coin_symbol = coin_symbol
		self.__balance_ratio = balance_ratio
		self.__leverage = leverage
		self.__duration = duration
		self.__is_prime = is_prime
	
	def price_multiple_make_profit(self, futures, coin_count, start_price, target_multiple):
		while True:
			with self.flag_lock:
				if not self.__safe_profit_flag:
					current_price = Futures.fetch_futures_coin_price_usdt(futures, self.__coin_symbol)
					if current_price / start_price > target_multiple:
						Futures.futures_market_short(futures, self.__coin_symbol, coin_count, True)
						self.__safe_profit_flag = True
						return
				
			time.sleep(5)
	
	def time_passed_make_profit(self, futures, safe_coin_count, coin_count, start_time, safe_duration, duration):
		while True:
			current_time = time.time()
			
			if current_time - start_time > duration:
				Futures.futures_market_short(futures, self.__coin_symbol, coin_count - safe_coin_count, True)
				return
			elif current_time - start_time > safe_duration:
				with self.flag_lock:
					if not self.__safe_profit_flag:
						Futures.futures_market_short(futures, self.__coin_symbol, safe_coin_count, True)
						self.__safe_profit_flag = True

			time.sleep(5)
		
	def run(self):
		if (not self.__is_prime) and Manager().get_has_position():
			return
		
		Manager().set_has_position(True)
		
		config = Config.load_config()
		futures = ccxt.binance({
			'apiKey': config['binance']['api_key'],
			'secret': config['binance']['secret_key'],
			'enableRateLimit': True,
			'options': {
				'defaultType': 'future',
			},
		})

		round_digit = 0
		
		#Futures.adjust_futures_leverage(futures, self.__coin_symbol, self.__leverage)
		
		balance_usdt = Futures.fetch_futures_usdt_balance(futures)
		coin_start_price = Futures.fetch_futures_coin_price_usdt(futures, self.__coin_symbol)
		coin_count = round(self.__balance_ratio * self.__leverage * balance_usdt / coin_start_price, round_digit)
		start_time = time.time()
		
		try:
			Futures.futures_market_long(futures, self.__coin_symbol, coin_count, False)
			
			half_coin_count = round(coin_count * 0.5, round_digit)
			
			time_passed_make_profit_thread = threading.Thread(target=CoinThread.time_passed_make_profit, args=(self, futures, half_coin_count, coin_count, start_time, int(self.__duration*0.5), self.__duration))
			time_passed_make_profit_thread.start()
			time_passed_make_profit_thread.join()
			
		except Exception as e:
			logger.logger.error(e)
		
		finally:
			Manager().set_has_position(False)