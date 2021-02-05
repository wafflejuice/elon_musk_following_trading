import ccxt
import json
import time

import exchange.exchange as exchange
import exchange.transaction as transaction
import database
import constants

def run():
	file = open('config.json', 'r')
	info = json.loads(file.read())
	file.close()
	
	binance = ccxt.binance({'apiKey': info['binance']['biannce_api_key'], 'secret': info['binance']['binance_secret_key']})
	futures = ccxt.binance({
		'apiKey': info['binance']['biannce_api_key'],
		'secret': info['binance']['binance_secret_key'],
		'enableRateLimit': True,
		'options': {
			'defaultType': 'future',
		},
	})

	database.Database().connect(info['mariaDB']['host'], info['mariaDB']['port'], info['mariaDB']['user'], info['mariaDB']['passwd'])
	
	database.Database().execute("CREATE DATABASE IF NOT EXISTS elon_musk_twitter")
	database.Database().execute("USE elon_musk_twitter")
	database.Database().execute("CREATE TABLE IF NOT EXISTS elon_musk_tweets(id VARCHAR(20) PRIMARY KEY, text TEXT)")
	database.Database().execute("ALTER TABLE elon_musk_tweets CONVERT TO CHARSET UTF8")
	
	database.Database().commit()
	
	telegram_get_updates_url = constants.TELEGRAM_GET_UPDATES_BASE_URL.format(info['telegram']['telegram_token'])
	telegram_send_message_url = constants.TELEGRAM_SEND_MESSAGE_BASE_URL.format(info['telegram']['telegram_token'])
	
	
	while True:
		
		# Check Elon Musk twitter
		
		# if coin-related tweet is found, make Long order
		
		# telegram me
		
		time.sleep(10)