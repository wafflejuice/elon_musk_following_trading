import pymysql

class Database(object):
	__db = None
	__cursor = None
	
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, "_instance"):
			cls._instance = super().__new__(cls)
		return cls._instance
	
	def connect(self, host, port, user, passwd):
		self.__db = pymysql.connect(host=host, port=port, user=user, passwd=passwd, charset='utf8')
		self.__cursor = self.__db.cursor()
		
	def execute(self, query):
		self.__cursor.execute(query)
		
	def commit(self):
		self.__db.commit()