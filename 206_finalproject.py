import unittest
import sqlite3
import requests
import json
import tweepy
import collections
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

# twitter handle requests and creating  string of full handle #similar to HW 5
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

#function that creates a tuple of important user information to be passed into the database easily
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

	u_id = response['id_str']
	name = "@"+response['screen_name']
	favorite_count = response['favourites_count']
	tup = (u_id, name, favorite_count)	

	return tup

#twitter search function that returns a list of tuples that contian information about each tweet
def twitter_search(search_term): #similar to project 2
	search_term = 'twitter_{}'.format(search_term)

	if search_term in CACHE_DICTION:
		response = CACHE_DICTION[search_term]

	else:
		response = api.search(q=search_term)
		CACHE_DICTION[search_term] = response
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
	tweets = []

	for tweet in response['statuses']:
		tweets.append(tweet)
	ls = []
	for tweet in tweets:
		tweet_id = tweet['id']
		text = tweet['text']
		u = tweet['user']
		user_name = "@"+u['screen_name']
		actor = search_term.strip('twitter_')
		favorites = tweet['favorite_count']
		retweets = tweet['retweet_count']
		tup = (tweet_id, text, user_name, actor, favorites, retweets)
		ls.append(tup)

	return ls

#using regex to make a list of user names found in strings of text
def get_twitter_users(tweet): #from project 3
	return [name[1:] for name in re.findall(r"@\w*", tweet)] #list of twitter names

#OMDB request to create a dictionary for each movie of information
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

#class to handle the return value of the OMDB search dictionary
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

	def movie_title(self): #returning the title
		return self.title

	def num_languages(self): #returning the number of languages
		num = self.languages.split(', ')
		return (len(num))

	def movie_director(self): #returning the Director
		return self.director

	def imdb_ID(self):
		return self.imdbID #PRIMARY KEY FOR DATABASE

	def list_of_actors(self): #list of actors
		return self.actors.split(', ')

	def num1_actor(self): #top actor from list
		return self.actors.split(', ')[0]

	def imdb_rating(self): #rating
		return float(self.imdbrating)

	def __str__(self): #string that has description of movie
		return "Plot description: {}\n".format(self.plot)

######### ORGANIZING THE DATA ###########
list_of_movies = ['the avengers', 'the big short', 'moonlight', 'la la land', 'deadpool', 'zootopia']
movie_requests = [omdb_search(movie) for movie in list_of_movies] #list comprehension of getting a dictionary of data for each movie
# print(movie_requests)
movie_class_instances = [Movie(movie) for movie in movie_requests] #list comprehension for movie instances
top_actors_of_movies_not_repeated = []
for movie in movie_class_instances:
	actor_name = movie.num1_actor() #getting the top actor for every movie
	if actor_name not in top_actors_of_movies_not_repeated:
		top_actors_of_movies_not_repeated.append(actor_name)

#passing information into database
movie_table = []
for movie in movie_class_instances:
	imdbID = movie.imdb_ID()
	title = movie.movie_title()
	director = movie.movie_director()
	languages = movie.num_languages()
	imdbRating = movie.imdb_rating()
	top_actor = movie.num1_actor()
	plot = movie.__str__()
	tup = (imdbID, title, director, languages, imdbRating, top_actor, plot)
	movie_table.append(tup)

dic_of_twitter_search = {actor: twitter_search(actor) for actor in top_actors_of_movies_not_repeated} #dictionary comprehension; actor name is key, and its value is a list of dictionaries containing tweets about each of the actors
abc = [] #creating a list of lists that contain tuples of twitter information; using this to make it easier to unpack to the datebase
for actor in top_actors_of_movies_not_repeated:
	abc.append(twitter_search(actor))
# print(json.dumps(abc, indent = 2))

#list of tuples containing twitter handles from text
handles_of_mentions = []
for ls in abc:
	for tup in ls:
		text = tup[1]
		names = get_twitter_users(text)
		handles_of_mentions.append(names)

#creating a list that does not repeat and finds user information for each mention
nz = []
for ls in handles_of_mentions:
	for handle in ls:
		try:
			names = user_info(handle)
		except:
			pass
		if names not in nz:
			nz.append(names)
		else:
			pass
for ls in abc:
	for tup in ls:
		name = tup[2]
		try:
			name_search = user_info(name)
		except:
			pass
		if name_search not in nz:
			nz.append(name_search)
		else:
			pass



######### CREATING THE DATABASE TABLES ###########
conn = sqlite3.connect('final_probject.db')
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS Tweets")
cur.execute("DROP TABLE IF EXISTS Users")
cur.execute("DROP TABLE IF EXISTS Movies")

#tweets db
table_spec = "CREATE TABLE IF NOT EXISTS "
table_spec += "Tweets (tweet_id PRIMARY KEY, text TEXT, screen_name TEXT, actor_search TEXT, favorites INTEGER, retweets INTEGER)"
cur.execute(table_spec)

#users db
table_spec = "CREATE TABLE IF NOT EXISTS "
table_spec += "Users (user_id PRIMARY KEY, screen_name TEXT, favorites INTEGER)"
cur.execute(table_spec)

#movies db
table_spec = "CREATE TABLE IF NOT EXISTS "
table_spec += "Movies (imdbID PRIMARY KEY, title TEXT, director TEXT, languages INTEGER, imdbRating INTEGER, top_actor TEXT, plot TEXT)"
cur.execute(table_spec)

######### EXECUTING THE DATA INTO THE TABLES ###########
statement = 'INSERT INTO Movies VALUES (?,?,?,?,?,?,?)'
for m in movie_table:
	cur.execute(statement, m)
conn.commit()


statement = 'INSERT INTO Tweets VALUES (?,?,?,?,?,?)'
for ls in abc:
	for x in ls:
		cur.execute(statement, x)
conn.commit()


statement = 'INSERT INTO Users VALUES (?,?,?)'
for tup in nz:
	cur.execute(statement, tup)
conn.commit()

######### QUERIES ###########
x = "SELECT Users.screen_name, Tweets.text , Tweets.retweets, Tweets.actor_search FROM Users INNER JOIN Tweets on Tweets.screen_name=Users.screen_name WHERE Tweets.retweets > 100"
cur.execute(x)
popular_actors = cur.fetchall()

diction = collections.defaultdict(list)
for tup in popular_actors:
	actor = tup[3]
	text = tup[1]
	diction[actor].append(text)
twitter_info_diction = dict(diction) #creates a dictionary with the keys of actors and their values that contain tweets with over 100 retweets
# print(json.dumps(twitter_info_diction, indent=2)) 

x = "SELECT Movies.title from Movies INNER JOIN Tweets on Movies.top_actor=Tweets.actor_search WHERE retweets > 500"
cur.execute(x)
movies = cur.fetchall()

dicto = {} #accumlated dictionary that grabbed the Title from movies that had actors tweeted about where retweets were greater than 500
for movie in movies:
	accum = 0
	if movie not in dicto:
		dicto[movie] = 1
	else:
		dicto[movie]+= 1

x = "SELECT Users.screen_name, Tweets.text, Tweets.retweets from Users INNER JOIN Tweets on Tweets.screen_name=Users.screen_name WHERE Tweets.retweets > 100"
cur.execute(x)
user_screen_names = cur.fetchall()
user_dict = {user[0]:[user[1], user[2]] for user in user_screen_names} #grabbed screen names of users that had over 100 retweets and created a dictionary with their name as the key, and the text and retweet number as the values

x = "SELECT Tweets.text FROM Movies INNER JOIN Tweets on Tweets.actor_search=Movies.top_actor"
cur.execute(x)
tweets_with_actor = cur.fetchall()

tweet_list = ["".join(tweet) for tweet in tweets_with_actor]

tags = [re.findall(r"#\w*", tweet) for tweet in tweet_list]

y = []
for tweet in tags:
	for t in tweet:
		y.append(t)

hashtags = {} #hashtags from all tweets and returns how many times it appeared in all of the tweets
for ht in y:
	if ht not in hashtags:
		hashtags[ht] = 1
	else:
		hashtags[ht] += 1
# print(hashtags) 

######### CSV OUTFILE ###########
outfile = open("finalproject_outfile.txt", "w")

outfile.write("MOVIES: 'the avengers', 'the big short', 'moonlight', 'la la land', 'deadpool', 'zootopia' \nTWITTER SUMMARY: searched the top actor of each movie and retreived the tweets \nDATE: 4/24/17\n\n\n\n")
outfile.write("1. Dictionary with top actors and their most popular tweets based on retweets:\n" + str(twitter_info_diction)+"\n\n\n\n")
outfile.write("2. Dictionary of movies in which teir top actor was tweeted about most\n" + str(dicto)+"\n\n\n\n")
outfile.write("3. Grabbed screen names and gave their top tweets and their retweet values\n" + str(user_dict)+"\n\n\n\n")
outfile.write("4. Most common hashtags from tweets from the top actor of each movie\n" + str(hashtags)+"\n\n\n\n")


outfile.close()
conn.close()
#########
print("*** OUTPUT OF TESTS BELOW THIS LINE ***\n")

class Twitter(unittest.TestCase):
	def test_get_twitter_name1(self):
		name = get_twitter_name("katy perry")
		self.assertEqual(name, "@katyperry", 'testing that it will return a username with @ sign')
	def test_get_twitter_name2(self):
		name = get_twitter_name("katy perry")
		self.assertEqual(name[0], "@", 'testing that there is a @ symbol at the beginning')
	def test_user_info1(self):
		user = user_info("@sadieladie980")
		self.assertEqual(len(user), 3, 'testing that there are three items')
	def test_user_info2(self):
		user = user_info("sadieladie980")
		self.assertEqual(user[0], '307390512', 'testing it will give the screen name id')
	def test_twitter_search1(self):
		search = twitter_search("university of michigan")
		self.assertEqual(type(search), type([]), 'testing it will return a list')
	def test_twitter_search2(self):
		search = twitter_search("university of michigan")
		self.assertEqual(type(search[0]), type((x,1,2)), 'testing it will return each tweet info in a tuple')
	def test_get_twitter_users1(self):
		get = get_twitter_users("@sadieladie980")
		self.assertEqual(get[0][0], "s", 'testing it will return without the @')
	def test_get_twitter_users2(self):
		get = get_twitter_users("@sadieladie980, @umsi")
		self.assertEqual(len(get), 2, 'testing that it will return two seperate strings')

class OMDB(unittest.TestCase):
	def test_omdb_search1(self):
		movie = omdb_search("the great outdoors")
		self.assertEqual(type(movie), type({}), 'testing that it will return a dictionary')
	def test_omdb_search2(self):
		movie = omdb_search("the great outdoors")
		self.assertEqual(movie["Released"], "17 Jun 1988")

class Movie(unittest.TestCase):
	def test_movie_class1(self):
		asdf = omdb_search("la la land")
		movie_s = Movie(asdf)
		self.assertEqual(movie_s.imdb_rating(), 8.3, "testing that this method will return a float")
	def test_movie_class2(self):
		movie = {"Title":"The Great Outdoors","Year":"1988","Rated":"PG","Released":"17 Jun 1988","Runtime":"91 min","Genre":"Comedy","Director":"Howard Deutch","Writer":"John Hughes","Actors":"Dan Aykroyd, John Candy, Stephanie Faracy, Annette Bening","Plot":"A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.","Language":"English","Country":"USA","Awards":"N/A","Poster":"https://images-na.ssl-images-amazon.com/images/M/MV5BZDVkNDQ3MDItZTBlOS00ZGU0LTk0ZDUtYmE2YzNmOTM4YzBhXkEyXkFqcGdeQXVyMjU5OTg5NDc@._V1_SX300.jpg","Ratings":[{"Source":"Internet Movie Database","Value":"6.6/10"},{"Source":"Rotten Tomatoes","Value":"40%"}],"Metascore":"N/A","imdbRating":"6.6","imdbVotes":"29,942","imdbID":"tt0095253","Type":"movie","DVD":"30 Jun 1998","BoxOffice":"N/A","Production":"Universal Pictures","Website":"N/A","Response":"True"}
		x = Movie(movie)
		self.assertEqual(x.__str__(), "Plot description: A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.")
	def test_movie_class3(self):
		movie = {"Title":"The Great Outdoors","Year":"1988","Rated":"PG","Released":"17 Jun 1988","Runtime":"91 min","Genre":"Comedy","Director":"Howard Deutch","Writer":"John Hughes","Actors":"Dan Aykroyd, John Candy, Stephanie Faracy, Annette Bening","Plot":"A Chicago man's hope for a peaceful family vacation in the woods is shattered when the annoying in-laws drop in.","Language":"English","Country":"USA","Awards":"N/A","Poster":"https://images-na.ssl-images-amazon.com/images/M/MV5BZDVkNDQ3MDItZTBlOS00ZGU0LTk0ZDUtYmE2YzNmOTM4YzBhXkEyXkFqcGdeQXVyMjU5OTg5NDc@._V1_SX300.jpg","Ratings":[{"Source":"Internet Movie Database","Value":"6.6/10"},{"Source":"Rotten Tomatoes","Value":"40%"}],"Metascore":"N/A","imdbRating":"6.6","imdbVotes":"29,942","imdbID":"tt0095253","Type":"movie","DVD":"30 Jun 1998","BoxOffice":"N/A","Production":"Universal Pictures","Website":"N/A","Response":"True"}
		x = Movie(movie)
		self.assertEqual(x.num1_actor(), "Dan Aykroyd")

class Other(unittest.TestCase):
	def test_list_of_movies(self):
		self.assertEqual(type(list_of_movies), type([]))
	def test_movie_requests(self):
		self.assertEqual(type(movie_requests), type([]))



if __name__ == "__main__":
	unittest.main(verbosity=2)