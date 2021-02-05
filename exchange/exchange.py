import constants

def fetch_binance_server_time(binance):
	binance_server_time = int(binance.public_get_time()['serverTime'])
	
	return binance_server_time


def fetch_binance_usdt_balance(binance):
	return binance.fetch_balance()[constants.USDT_SYMBOL]['free']

def fetch_binance_coin_count(binance, coin):
	return binance.fetch_balance()[coin.get_coin_symbol()]['free']

def fetch_binance_coin_price_usdt(binance, coin):
	return binance.fetch_ticker(coin.get_binance_coin_usdt_id())['last']

def fetch_binance_coin_value_usdt(binance, coin):
	binance_coin_count = fetch_binance_coin_count(binance, coin)
	binance_coin_price_usdt = fetch_binance_coin_price_usdt(binance, coin)
	binance_coin_value_usdt = binance_coin_count * binance_coin_price_usdt
	
	return binance_coin_value_usdt


def fetch_futures_usdt_balance(futures):
	futures_balance = futures.fapiPrivateGetBalance()
	futures_balance_chunk = list(filter(lambda x: x['asset'] == constants.USDT_SYMBOL, futures_balance))[0]
	futures_usdt_balance = float(futures_balance_chunk['balance'])
	
	return futures_usdt_balance

def fetch_futures_coin_position(futures, coin):
	futures_positions = futures.fetch_positions()
	# If take same position multiple times, they are combined.
	futures_coin_position = list(filter(lambda x: x['symbol'] == coin.get_futures_coin_usdt_id(), futures_positions))[0]
	# 'positionAmt' is + (long), - (short)
	futures_coin_position_amount = float(futures_coin_position['positionAmt'])
	
	return futures_coin_position_amount

def fetch_futures_coin_price_usdt(futures, coin):
	futures_coin_ticker = futures.fapiPublicGetTickerPrice({
		'symbol': coin.get_futures_coin_usdt_id()
	})
	futures_coin_price = float(futures_coin_ticker['price'])
	
	return futures_coin_price

def adjust_futures_leverage(futures, coin, leverage):
	if leverage < 1:
		raise ValueError("leverage should be at least x1")
	
	futures.fapiPrivatePostLeverage({
		'symbol': coin.get_futures_coin_usdt_id(),
		'leverage': leverage,
	})
	
	coin.set_futures_coin_leverage(leverage)