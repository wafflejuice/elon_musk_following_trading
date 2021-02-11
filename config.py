import json

class Config:
	CONFIG_FILE = 'config.json'
	
	@classmethod
	def load_config(cls):
		file = open(cls.CONFIG_FILE, 'r')
		config = json.loads(file.read())
		file.close()
		
		return config