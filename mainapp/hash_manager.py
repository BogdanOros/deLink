import hashlib


class HashManager:

	def __init__(self):
		self.hash = hashlib.md5()

	def hash_value(self, value_to_hash):
		self.hash.update(value_to_hash)
		return self.hash.hexdigest()