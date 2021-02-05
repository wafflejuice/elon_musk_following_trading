import constants

import exchange.exchange as exchange

def futures_market_short(futures, coin, coin_count, reduce_only):
	if reduce_only:
		futures_coin_position_absolute_amount = abs(exchange.fetch_futures_coin_position(futures, coin))
		
		futures.fapiPrivatePostOrder({
			'symbol': coin.get_futures_coin_usdt_id(),
			'side': 'SELL',
			'type': 'MARKET',
			'quantity': futures_coin_position_absolute_amount,
			'reduceOnly': 'true',
		})
	else:
		futures.fapiPrivatePostOrder({
			'symbol': coin.get_futures_coin_usdt_id(),
			'side': 'SELL',
			'type': 'MARKET',
			'quantity': coin_count,
		})
	
def futures_market_long(futures, coin, coin_count, reduce_only):
	if reduce_only:
		futures_coin_position_absolute_amount = abs(exchange.fetch_futures_coin_position(futures, coin))
		
		futures.fapiPrivatePostOrder({
			'symbol': coin.get_futures_coin_usdt_id(),
			'side': 'BUY',
			'type': 'MARKET',
			'quantity': futures_coin_position_absolute_amount,
			'reduceOnly': 'true',
		})
	else:
		futures.fapiPrivatePostOrder({
			'symbol': coin.get_futures_coin_usdt_id(),
			'side': 'BUY',
			'type': 'MARKET',
			'quantity': coin_count,
		})
	
# direction_type 1: Binance->Futures, 2: Futures->Binance
# TODO : balance check
def internal_transfer_usdt(binance, amount_usdt, direction_type):
	start_time = exchange.fetch_binance_server_time(binance)
	
	transaction = binance.sapi_post_futures_transfer({
		'asset': constants.USDT_SYMBOL,
		'amount': amount_usdt,
		'type': direction_type,
	})
	
	# Check if transaction is finished
	# TODO : Of course, need to make it async
	while True:
		futures_transaction_history = binance.sapi_get_futures_transfer({
			'startTime': start_time - constants.EPOCH_TIME_HOUR_MS,  # Because timestamp is floor(serverTime) by second, subtract 1 hour
			'current': 1,
			'asset': constants.USDT_SYMBOL,
		})
		
		# Check tranId & status
		if futures_transaction_history['total'] > 0:
			futures_last_transaction = futures_transaction_history['rows'][-1]
			
			if futures_last_transaction['tranId'] == transaction['tranId'] and futures_last_transaction['status'] == 'CONFIRMED':
				# Transaction is finished
				return
			
def transfer_usdt(binance, amount_usdt):
	internal_transfer_usdt(binance, amount_usdt, 1)
	
def convert_usdt(binance, amount_usdt):
	internal_transfer_usdt(binance, amount_usdt, 2)

def convert_whole(binance, futures):
	futures_usdt_balance_amount = exchange.fetch_futures_usdt_balance(futures)
	convert_usdt(binance, futures_usdt_balance_amount)