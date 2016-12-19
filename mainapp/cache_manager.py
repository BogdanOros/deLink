import redis
import pickle
import json
from bson import json_util


class CacheManager(object):

	def __init__(self):
		self.r = redis.Redis(host='localhost', port=6379)
		self.r.flushall()

	def cache_last_visited_folder(self, key, value):
		self.r.set(str(key) + 'u', pickle.dumps(value))

	def get_last_visited_folder(self, key):
		data = self.r.get(str(key) + 'u')
		if data:
			return pickle.loads(data)

	def clear_last_visited_folder(self, key):
		self.r.delete(str(key) + 'u')

	def cache_folder(self, key, data):
		self.r.set(str(key), pickle.dumps(data))
		self.r.incr('cached_folders')

	def get_folder(self, key):
		data = self.r.get(str(key))
		if data:
			return pickle.loads(data)

	def clear_folders_cache(self, key):
		data = self.r.get(str(key))
		if data:
			self.r.delete(str(key))
			self.r.decr('cached_folders')

	def cache_search_query(self, user_id, key, data):
		self.r.hset(user_id, key, pickle.dumps(data))
		self.r.incr('cached_search')

	def get_data_by_query(self, user_id, key):
		data = self.r.hget(user_id, key)
		if data:
			return pickle.loads(data)

	def clear_search_cache(self, user_id):
		count_of_users_keys = len(self.r.hkeys(user_id))
		self.r.hdel(user_id)
		self.r.decr('cached_search', count_of_users_keys)

	def cache_statistics(self):
		# all_keys = len(self.r.keys())
		search_keys, folder_keys = 0, 0
		search = self.r.get('cached_search')
		if search:
			search_keys = search
		folder = self.r.get('cached_folders')
		if folder:
			folder_keys = folder

		all = int(search_keys) + int(folder_keys)

		print ('All: ' + str(all))
		print ('Search content: ' + str(search_keys))
		print ('Folder keys: ' + str(folder_keys))