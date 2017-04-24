from bottle import run, get, post, request
import csv
import random
import urllib.parse
import urllib.request
import bs4
import requests
import numpy as np
import yaml


#FILES
moviesFileName = 'Movies.csv'
#ratingsFileName = 'Ratings.csv'
normalizedRatingFileName = 'NormalizedRatingDictionary.csv'
likedUsersFileName = 'LikedUsers.csv'

file1 = open(moviesFileName, "rt", encoding="utf-8")
movieReader = csv.reader(file1)

#file2 = open(ratingsFileName, "rt", encoding="utf-8")
#ratingReader = csv.reader(file2)

file3 = open(normalizedRatingFileName, "rt", encoding="utf-8")
normalizedRatingReader = csv.reader(file3)

file4 = open(likedUsersFileName, "rt", encoding="utf-8")
LikedUsersReader = csv.reader(file4)


#GLOBAL VARIABLES
global userGenreCounter
userGenreCounter = {'Comedy' : 0, 'Action' : 0, 'Sci-Fi' : 0, 'Drama' : 0, 'Romance' : 0, 'Thriller' : 0, 'Mystery' : 0, 'Horror' : 0, 'Animation' : 0, 'Adventure' : 0}
#For Content Filtering Method

global BestMatchingMovies
BestMatchingMovies = {} #Stores IDs and IMDb URLs of best matching movies through content filtering

global CollaborativeFilteredMovies
CollaborativeFilteredMovies = {} #Stores IDs and IMDb URLs of the best matching movies through collaborative Filtering

global normalizedUserRatings
normalizedUserRatings = {}



#Post request which accepts selected movies and ratings
#Selected movies and ratings in JSON format
#No output
@post('/selectedmovies')
def GetMovieListAndGenreCount():

    global userSelectedMovies
    userSelectedMovies = request.json.get('selectedmovieslist')

    GenreCounterUpdater(userSelectedMovies)
    RatingNormalizer(userSelectedMovies)
    ContentFiltering()
    CollaborativeFiltering()



#Updates the genre count based on selected movies and ratings
#Takes selected movies and rating dictionary as input
#No output
def GenreCounterUpdater(userSelectedMovies):

    for genre in userGenreCounter:
        userGenreCounter[genre] = 0 #Resetting all genre counts to zero

    for userMovieID in userSelectedMovies:
        file1.seek(0)
        for row in movieReader:
            if str(row[0]) == str(userMovieID):
                for genre in row[2].split('|'):
                    if genre in userGenreCounter:
                        userGenreCounter[genre] += userSelectedMovies[userMovieID]
                break



#Normalizes the user's ratings
#Takes user selected movies as input
#No output
def RatingNormalizer(userSelectedMovies):

    total = 0
    i = 0
    for movie in userSelectedMovies:
        total += userSelectedMovies[movie]
        i = i + 1
    average = total / i
    
    for movie in userSelectedMovies:
        normalizedUserRatings.update({str(movie) : userSelectedMovies[movie] - average})



#Finds the top 10 recommended movies by content filtering
#Takes genre count dictionary as input
#No output
def ContentFiltering():

    notEmpty = False
    ContentFilteredMovies = {}
    BestMatchingMovies = {}
    SortedFilteredMovies = []

    file1.seek(0)
    for row in movieReader:
        TotalGenreMatch = 0
        for genre in row[2].split('|'):
            if str(genre) in userGenreCounter:
                TotalGenreMatch += userGenreCounter[genre]

        ContentFilteredMovies.update({row[0] : TotalGenreMatch})

    SortedFilteredMovies = sorted(ContentFilteredMovies, key=ContentFilteredMovies.__getitem__, reverse = True)

    for i in range(0, 10):
        url = GetUrl(SortedFilteredMovies[i])
        BestMatchingMovies.update({SortedFilteredMovies[i] : url})
        i = i + 1
    print(BestMatchingMovies)


#Returns the IMDb URL of the movie
#Takes movie ID as input
#No output
def GetUrl(movieID):

    file1.seek(0)
    for row in movieReader:
        if str(row[0]) == str(movieID):
            movieSearchTerm = row[1] + " imdb"
            SearchUrl = r'https://www.google.co.in/search?q=' + urllib.parse.quote_plus(movieSearchTerm)
            searchResult = requests.get(SearchUrl)
            searchResult.raise_for_status()
            soup = bs4.BeautifulSoup(searchResult.text, 'html.parser')
            IMDbID = str(soup.find('cite'))[32:41]
            url = "http://www.imdb.com/title/" + IMDbID
    return url



#Creates a dictionary of recommended movies through collaborative filtering
#No input
#No output
def CollaborativeFiltering():

    CollaborativeFilteredMovies = {}
    similarUser = FindSimilarUser(userSelectedMovies)
    file3.seek(0)
    i = 0
    for row in normalizedRatingReader:
        if str(row[0]) == str(similarUser):
            tempDict = yaml.load(row[1])
            for movie in tempDict:
                if i == 4:
                    break
                i = i + 1
                if tempDict[movie] > 0:
                    url = GetUrl(movie)
                    CollaborativeFilteredMovies.update({movie : url})
    print(CollaborativeFilteredMovies)


#Finds a similar user based on good ratings for the same movie
#Takes user selected movies as input
#No output
def FindSimilarUser(userSelectedMovies):

    mostLikedMovie = FindMostLikedMovie(normalizedUserRatings)
    file4.seek(0)
    for row2 in LikedUsersReader:
        if str(row2[0]) == str(mostLikedMovie):
            tempDict = yaml.load(row2[1])
            if tempDict:
                for user in tempDict:
                    if PearsonCoefficient(int(user)) > '''threshold''':
                        return user



#Searches for the most liked movie 
#Takes normalized user ratings as input
#NO output
def FindMostLikedMovie(normalizedUserRatings):

    mostLiked = next(iter(normalizedUserRatings))
    for movie in normalizedUserRatings:
        if normalizedUserRatings[movie] > normalizedUserRatings[mostLiked]:
            mostLiked = movie

    return mostLiked



#Calculates the Pearson Correlatin Coefficient between new user and recorded user
#Takes user ID of recorded user as input
#No output
def PearsonCoefficient(userID):

    file3.seek(0)
    for row in normalizedRatingReader:
        if str(row[0]) == str(userID):
            temp = []
            userRatingArray = []
            user = userSelectedMovies
            comp = yaml.load(row[1])
            for movie in comp:
                if str(movie) not in userSelectedMovies:
                    userRatingArray.append(0)
                else:
                    userRatingArray.append(userSelectedMovies[movie])
                temp.append(yaml.load(row[1])[movie])
            for movie in userSelectedMovies:
                if str(movie) not in yaml.load(row[1]):
                    userRatingArray.append(userSelectedMovies[movie])
                    temp.append(0)

            a = np.array(userRatingArray)
            b = np.array(temp)

            cosine = (np.dot(a, b)) / ((np.sqrt((a * a).sum())) * np.sqrt((b * b).sum()))

            return cosine


#Generates a dictionary of recommended movies from ContentFilteredMovies and CollaborativeFilteredMovies
#No input
#No output
@get('/recommended')
def GetRecommended():

    recommendedMovies = {}
    print(BestMatchingMovies)
    print(CollaborativeFilteredMovies)
    for movieID in BestMatchingMovies:
        if str(movieID) not in str(userSelectedMovies):
            recommendedMovies.update({movieID : BestMatchingMovies[movieID]})

    for movieID in CollaborativeFilteredMovies:
        if str(movieID) not in str(userSelectedMovies):
            recommendedMovies.update({movieID : CollaborativeFilteredMovies[movieID]})


    return recommendedMovies


run(reloader=True, debug=True)
