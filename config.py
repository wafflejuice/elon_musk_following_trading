import json

import constants

class Config:
	@staticmethod
	def load_config():
		file = open(constants.CONFIG_FILE, 'r')
		config = json.loads(file.read())
		file.close()
		
		return config