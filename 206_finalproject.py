import unittest
import json
import tweepy
import requests

CACHE_FNAME = "cache_info.json"
try:
	cache_file = open(CACHE_FNAME, 'r')
	cache_contents = cache_file.read()
	CACHE_DICTION = json.loads(cache_contents)
	cache_file.close()

except:
	CACHE_DICTION = {}















#########
print("*** OUTPUT OF TESTS BELOW THIS LINE ***\n")

class PartOne(unittest.TestCase):
	def test1(self):
		fpt = open("cache_info.json","r")
		fpt_str = fpt.read()
		fpt.close()
		obj = json.loads(fpt_str)
		self.assertEqual(type(obj),type({"hi":"bye"}))

if __name__ == "__main__":
	unittest.main(verbosity=2)