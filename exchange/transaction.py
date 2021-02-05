import exchange.exchange as exchange
from exchange.coin import Coin

def futures_market_short(futures, coin_symbol, coin_count, reduce_only):
	if reduce_only:
		futures.fapiPrivatePostOrder({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'side': 'SELL',
			'type': 'MARKET',
			'quantity': coin_count,
			'reduceOnly': 'true',
		})
	else:
		futures.fapiPrivatePostOrder({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'side': 'SELL',
			'type': 'MARKET',
			'quantity': coin_count,
		})
	
def futures_market_long(futures, coin_symbol, coin_count, reduce_only):
	if reduce_only:
		futures.fapiPrivatePostOrder({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'side': 'BUY',
			'type': 'MARKET',
			'quantity': coin_count,
			'reduceOnly': 'true',
		})
	else:
		futures.fapiPrivatePostOrder({
			'symbol': Coin.get_futures_coin_usdt_id(coin_symbol),
			'side': 'BUY',
			'type': 'MARKET',
			'quantity': coin_count,
		})