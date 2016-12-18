import redis
import pickle


class CacheManager(object):

	def __init__(self):
		self.r = redis.Redis(host='localhost', port=6379)
		self.r.flushall()

	def cache_data(self, key, data):
		self.r.set(str(key), pickle.dumps(data))

	def get_data(self, key):
		data = self.r.get(str(key))
		if data:
			return pickle.loads(data)

	def clear_cache(self, key):
		data = self.r.get(str(key))
		if data:
			self.r.delete(str(key))