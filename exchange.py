import ccxt
import time
#import multiprocessing
import threading

from config import Config
import constants
import logger
from telegram import Telegram


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
		
		return res

	@staticmethod
	def futures_market_long(coin_symbol, coin_count, reduce_only):
		return Futures().futures_market_order(coin_symbol, coin_count, 'BUY', reduce_only)

	@staticmethod
	def futures_market_short(coin_symbol, coin_count, reduce_only):
		return Futures().futures_market_order(coin_symbol, coin_count, 'SELL', reduce_only)
	
	def futures_stop_market_order(self, coin_symbol, coin_count, side, stop_price):
		res = self.futures.fapiPrivatePostOrder({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'side': side,
			'type': 'STOP_MARKET',
			'quantity': coin_count,
			'stopPrice': stop_price,
		})
		logger.logger.info(res)
		
		return res
	
	def futures_cancel_order(self, coin_symbol, order_id):
		res = self.futures.fapiPrivateDeleteOrder({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'orderId': order_id,
		})
		logger.logger.info(res)
		
		return res
		
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

	def run_update_price_periodical(self, period):
		t = threading.Thread(target=self.update_price_periodical, args=(period,))
		t.start()
	
	def update_price_periodical(self, period):
		while True:
			try:
				self.update_price()
				logger.logger.info("[{}] stored coin price = {}".format(time.strftime('%c', time.localtime(time.time())), self.doge_price_store))
				
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
			price = self.doge_price_store
			coin_count = int(balance / price)
			
			try:
				market_long_res = Futures().futures_market_long(symbol, coin_count, False)
				logger.logger.info(market_long_res)
				
				text_bundle = []
				
				market_long_text = 'betting balance={}, stored price={}, coin count={}'.format(balance, price, coin_count)
				text_bundle.append(market_long_text)
				logger.logger.info(market_long_text)
				
				latest_price = Futures().fetch_futures_coin_price_usdt(symbol)
				stop_price = int((latest_price * 0.99) * 100000) / 100000.0
				stop_order_res = Futures().futures_stop_market_order(symbol, coin_count, 'SELL', stop_price)
				logger.logger.info(stop_order_res)
				
				stop_text = 'latest price={}, stop price={}'.format(latest_price, stop_price)
				text_bundle.append(stop_text)
				logger.logger.info(stop_text)
				
				Telegram.send_message(Telegram.fetch_chat_id(), Telegram.args_to_message(text_bundle))
				
				time.sleep(duration)
				
				market_short_res = Futures().futures_market_short(symbol, coin_count, True)
				logger.logger.info(market_short_res)
				
				cancel_stop_order_res = Futures().futures_cancel_order(symbol, stop_order_res['orderId'])
				logger.logger.info(cancel_stop_order_res)
				
				self.update_price()
			
			except Exception as e:
				logger.logger.error(e)
				Telegram.send_message(Telegram.fetch_chat_id(), e)
