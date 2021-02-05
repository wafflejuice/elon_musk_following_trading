from exchange.coin import Coin
import constants

def fetch_binance_usdt_balance(binance):
	return binance.fetch_balance()[constants.USDT_SYMBOL]['free']

def fetch_futures_usdt_balance(futures):
	futures_balance = futures.fapiPrivateGetBalance()
	futures_balance_chunk = list(filter(lambda x: x['asset'] == constants.USDT_SYMBOL, futures_balance))[0]
	futures_usdt_balance = float(futures_balance_chunk['balance'])
	
	return futures_usdt_balance

def fetch_futures_coin_position(futures, coin_symbol):
	futures_positions = futures.fetch_positions()
	# If take same position multiple times, they are combined.
	futures_coin_position = list(filter(lambda x: x['symbol'] == Coin.get_futures_coin_usdt_id(coin_symbol), futures_positions))[0]
	# 'positionAmt' is + (long), - (short)
	futures_coin_position_amount = float(futures_coin_position['positionAmt'])
	
	return futures_coin_position_amount

def fetch_futures_coin_price_usdt(futures, coin_symbol):
	futures_coin_ticker = futures.fapiPublicGetTickerPrice({
		'symbol': Coin.get_futures_coin_usdt_id(coin_symbol)
	})
	futures_coin_price = float(futures_coin_ticker['price'])
	
	return futures_coin_price

def adjust_futures_leverage(futures, coin_symbol, leverage):
	if leverage < 1:
		raise ValueError("leverage should be at least x1")
	
	futures.fapiPrivatePostLeverage({
		'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
		'leverage': leverage,
	})