import unittest
import sqlite3
import requests
import json
import tweepy
import twitter_info
import re

#twitter info
consumer_key = twitter_info.consumer_key
consumer_secret = twitter_info.consumer_secret
access_token = twitter_info.access_token
access_token_secret = twitter_info.access_token_secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

#twitter request
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

#caching functions
CACHE_FNAME = "206_final_project_cache.json"
try:
	cache_file = open(CACHE_FNAME, 'r')
	cache_contents = cache_file.read()
	CACHE_DICTION = json.loads(cache_contents)
	cache_file.close()

except:
	CACHE_DICTION = {}

# twitter handle requests #from HW 5
def get_twitter_name(actor_name):
	if actor_name in CACHE_DICTION:
		# print("\nUSING CACHE\n")
		response = CACHE_DICTION[actor_name]

	else:
		# print("\nFETCHING DATA\n")
		response = api.search_users(q=actor_name)
		CACHE_DICTION[actor_name] = response
		# print("fetching\n")
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
	for dic in response:
		if dic['verified'] == True:
			return '@'+dic['screen_name']

def user_info(user_name):
	if user_name in CACHE_DICTION:
		response = CACHE_DICTION[user_name]

	else:
		response = api.get_user(user_name)
		CACHE_DICTION[user_name] = response
		# print("fetching\n")
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()

	return response

def twitter_search(search_term):
	if search_term in CACHE_DICTION:
		response = CACHE_DICTION[search_term]

	else:
		response = api.search(q=search_term)
		CACHE_DICTION[search_term] = response
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()

	return response['statuses']

def twitter_neighborhood(twitter_name):
	pass #still not sure about what the "neighborhood" consists of and what tweepy api method to use

#OMDB request
def omdb_search(move_title):
	base_url = "http://www.omdbapi.com/?"
	params_dict = {}
	params_dict['t'] = move_title
	response = requests.get(base_url, params=params_dict)

	if response in CACHE_DICTION:
		CACHE_DICTION[movie_title] = response

	else:
		response = json.loads(response.text)
		CACHE_DICTION[move_title] = response
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
	return response

#class to handle the return value of the OMDB search
class Movie():
	def __init__(self,movie_dict):
		self.title = movie_dict['Title']
		self.release_date = movie_dict['Released']
		self.rated = movie_dict["Rated"]
		self.languages = movie_dict['Language']
		self.runtime = movie_dict['Runtime']
		self.director = movie_dict['Director']
		self.actors = movie_dict['Actors']
		self.awards = movie_dict['Awards']
		self.genre = movie_dict['Genre']
		self.plot = movie_dict['Plot']
		self.imdbrating = movie_dict['imdbRating']
		self.ratings = movie_dict['Ratings']
		self.imdbID = movie_dict['imdbID'] #MAKE THIS PRIMARY KEY

	def movie_title(self):
		return self.title

	def num_languages(self):
		num = self.languages.split(', ')
		return (len(num))

	def movie_director(self):
		return self.director

	def imdb_ID(self):
		return self.imdbID #PRIMARY KEY FOR DATABASE

	def list_of_actors(self):
		return self.actors.split(', ')

	def num1_actor(self):
		return self.actors.split(', ')[0]

	def imdb_rating(self):
		return float(self.imdbrating)

	def movie_genres(self):
		return self.genre.split(', ')

	def released(self):
		return self.release_date

	def __str__(self):
		return "Plot description: {}\n".format(self.plot)

	def rating_sources(self):
		sources = []
		for dic in self.ratings:
			source = dic['Source']
			value = dic['Value']
			tup = (source, value)
			sources.append(tup)
		return sources



list_of_movies = ['the avengers', 'the big short', 'moonlight', 'manchester by the sea', 'zootopia', "captain america: civil war", 'la la land']
movie_requests = [omdb_search(movie) for movie in list_of_movies] #list comprehension
# print(movie_requests)
movie_class_instances = [Movie(movie) for movie in movie_requests] #list comprehension for movie instances
top_actors_of_movies_not_repeated = []
for movie in movie_class_instances:
	actor_name = movie.num1_actor() #getting the top actor for every movie
	if actor_name not in top_actors_of_movies_not_repeated:
		top_actors_of_movies_not_repeated.append(actor_name)
# print(top_actors_of_movies_not_repeated)
twitter_name_search = [get_twitter_name(actor) for actor in top_actors_of_movies_not_repeated] #retrieving twitter name for each top actor fromt the movie instances; list comprehension
# print(twitter_name_search)




conn = sqlite3.connect('final_probject.db')
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS Tweets")
cur.execute("DROP TABLE IF EXISTS Users")
cur.execute("DROP TABLE IF EXISTS Movies")

#tweets db
table_spec = "CREATE TABLE IF NOT EXISTS "
table_spec += "Tweets (tweet_id PRIMARY KEY, text TEXT, screen_name TEXT, movie_search TEXT, favorites INTEGER, retweets INTEGER)"
cur.execute(table_spec)

#users db
table_spec = "CREATE TABLE IF NOT EXISTS "
table_spec += "Users (user_id PRIMARY KEY, screen_name TEXT, favorites INTEGER)"
cur.execute(table_spec)

#movies db
table_spec = "CREATE TABLE IF NOT EXISTS "
table_spec += "Movies (imdbID PRIMARY KEY, title TEXT, director TEXT, languages INTEGER, imdbRating INTEGER, top_actor TEXT)"
cur.execute(table_spec)

#passing information into database
movie_table = []
for movie in movie_class_instances:
	imdbID = movie.imdb_ID()
	title = movie.movie_title()
	director = movie.movie_director()
	languages = movie.num_languages()
	imdbRating = movie.imdb_rating()
	top_actor = movie.num1_actor()
	tup = (imdbID, title, director, languages, imdbRating, top_actor)
	movie_table.append(tup)

statement = 'INSERT INTO Movies VALUES (?,?,?,?,?,?)'
for m in movie_table:
	cur.execute(statement, m)

conn.commit()



conn.close()
#########
print("*** OUTPUT OF TESTS BELOW THIS LINE ***\n")

class Twitter(unittest.TestCase):
	def test_get_twitter_name1(self):
		name = get_twitter_name("katy perry")
		self.assertEqual(name, "@katyperry", 'testing that it will return a username with @ sign')
	def test_get_twitter_name2(self):
		name = get_twitter_name("katy perry")
		self.assertEqual(type(name), type(""), 'testing that the return value will be a string')
	def test_get_twitter_name3(self):
		name = get_twitter_name("katy perry")
		self.assertEqual(name[0], "@", 'testing that there is a @ symbol at the beginning')
class OMDB(unittest.TestCase):
	def test_omdb_search1(self):
		movie = omdb_search("the great outdoors")
		self.assertEqual(type(movie), type({}), 'testing that it will return a dictionary')
class Movie(unittest.TestCase):
	def test_movie_class1(self):
		movie = {"Title":"The Great Outdoors","Year":"1988","Rated":"PG","Released":"17 Jun 1988","Runtime":"91 min","Genre":"Comedy","Director":"Howard Deutch","Writer":"John Hughes","Actors":"Dan Aykroyd, John Candy, Stephanie Faracy, Annette Bening","Plot":"A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.","Language":"English","Country":"USA","Awards":"N/A","Poster":"https://images-na.ssl-images-amazon.com/images/M/MV5BZDVkNDQ3MDItZTBlOS00ZGU0LTk0ZDUtYmE2YzNmOTM4YzBhXkEyXkFqcGdeQXVyMjU5OTg5NDc@._V1_SX300.jpg","Ratings":[{"Source":"Internet Movie Database","Value":"6.6/10"},{"Source":"Rotten Tomatoes","Value":"40%"}],"Metascore":"N/A","imdbRating":"6.6","imdbVotes":"29,942","imdbID":"tt0095253","Type":"movie","DVD":"30 Jun 1998","BoxOffice":"N/A","Production":"Universal Pictures","Website":"N/A","Response":"True"}
		x = Movie(movie)
		self.assertEqual(type(movie.imdb_rating()), type(float("6.6")), "testing that this method will return a float")
	def test_movie_class2(self):
		movie = {"Title":"The Great Outdoors","Year":"1988","Rated":"PG","Released":"17 Jun 1988","Runtime":"91 min","Genre":"Comedy","Director":"Howard Deutch","Writer":"John Hughes","Actors":"Dan Aykroyd, John Candy, Stephanie Faracy, Annette Bening","Plot":"A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.","Language":"English","Country":"USA","Awards":"N/A","Poster":"https://images-na.ssl-images-amazon.com/images/M/MV5BZDVkNDQ3MDItZTBlOS00ZGU0LTk0ZDUtYmE2YzNmOTM4YzBhXkEyXkFqcGdeQXVyMjU5OTg5NDc@._V1_SX300.jpg","Ratings":[{"Source":"Internet Movie Database","Value":"6.6/10"},{"Source":"Rotten Tomatoes","Value":"40%"}],"Metascore":"N/A","imdbRating":"6.6","imdbVotes":"29,942","imdbID":"tt0095253","Type":"movie","DVD":"30 Jun 1998","BoxOffice":"N/A","Production":"Universal Pictures","Website":"N/A","Response":"True"}
		x = Movie(movie)
		self.assertEqual(movie.__str__(), "Plot description: A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.")
	def test_movie_class3(self):
		movie = {"Title":"The Great Outdoors","Year":"1988","Rated":"PG","Released":"17 Jun 1988","Runtime":"91 min","Genre":"Comedy","Director":"Howard Deutch","Writer":"John Hughes","Actors":"Dan Aykroyd, John Candy, Stephanie Faracy, Annette Bening","Plot":"A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.","Language":"English","Country":"USA","Awards":"N/A","Poster":"https://images-na.ssl-images-amazon.com/images/M/MV5BZDVkNDQ3MDItZTBlOS00ZGU0LTk0ZDUtYmE2YzNmOTM4YzBhXkEyXkFqcGdeQXVyMjU5OTg5NDc@._V1_SX300.jpg","Ratings":[{"Source":"Internet Movie Database","Value":"6.6/10"},{"Source":"Rotten Tomatoes","Value":"40%"}],"Metascore":"N/A","imdbRating":"6.6","imdbVotes":"29,942","imdbID":"tt0095253","Type":"movie","DVD":"30 Jun 1998","BoxOffice":"N/A","Production":"Universal Pictures","Website":"N/A","Response":"True"}
		x = Movie(movie)
		self.assertEqual(movie.num1_actor(), "Dan Aykroyd")
class Other(unittest.TestCase):
	def test_list_of_movies(self):
		self.assertEqual(type(list_of_movies), type([]))
	def test_movie_requests(self):
		self.assertEqual(type(movie_requests), type([]))



if __name__ == "__main__":
	unittest.main(verbosity=2)