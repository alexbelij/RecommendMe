from bottle import run, get, post, request
import csv
import urllib.parse
import urllib.request
import bs4
import requests
import numpy as np
import yaml


#FILES
moviesFileName = 'Movies.csv'
normalizedRatingFileName = 'NormalizedRatingDictionary.csv'

file1 = open(moviesFileName, "rt", encoding="utf-8")
movieReader = csv.reader(file1)

file2 = open(normalizedRatingFileName, "rt", encoding="utf-8")
normalizedRatingReader = csv.reader(file2)


#GLOBAL VARIABLES
global userGenreCounter
userGenreCounter = {'Comedy' : 0, 'Action' : 0, 'Sci-Fi' : 0, 'Drama' : 0, 'Romance' : 0, 'Thriller' : 0, 'Mystery' : 0, 'Horror' : 0, 'Animation' : 0, 'Adventure' : 0}
#For Content Filtering Method

global ContentFilteredMovies
ContentFilteredMovies = [] #List to store IDs of best matching movies through content filtering

global CollaborativeFilteredMovies
CollaborativeFilteredMovies = [] #List to store IDs of the best matching movies through collaborative Filtering

global normalizedUserRatings
normalizedUserRatings = {} #Dictionary to store the movie ID and normalized ratings of the user



#Post request which accepts selected movies and ratings
#Selected movies and ratings in JSON format
#No output
@post('/selectedmovies')
def GetMovieListAndGenreCount():

    global userSelectedMovies
    userSelectedMovies = request.json.get('selectedmovieslist')

    GenreCounterUpdater(userSelectedMovies)
    RatingNormalizer(userSelectedMovies)



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
    ContentFiltering()



#Normalizes the user's ratings
#Takes user selected movies as input
#No output
def RatingNormalizer(userSelectedMovies):

    total = 0
    count = 0
    for movie in userSelectedMovies:
        total += userSelectedMovies[movie]
        count = count + 1
    average = total / count
    
    for movie in userSelectedMovies:
        normalizedUserRatings.update({str(movie) : userSelectedMovies[movie] - average})

    CollaborativeFiltering()



#Finds the top 10 recommended movies by content filtering
#Takes genre count dictionary as input
#No output
def ContentFiltering():

    notEmpty = False
    BestMovies = {}
    SortedFilteredMovies = []

    file1.seek(0)
    for row in movieReader:
        TotalGenreMatch = 0
        for genre in row[2].split('|'):
            if str(genre) in userGenreCounter:
                TotalGenreMatch += userGenreCounter[genre]

        BestMovies.update({row[0] : TotalGenreMatch})

    SortedFilteredMovies = sorted(BestMovies, key=BestMovies.__getitem__, reverse = True)

    for i in range(0, 10):
        if SortedFilteredMovies[i] not in userSelectedMovies:
            ContentFilteredMovies.append(SortedFilteredMovies[i])
            i = i + 1


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

    tempDict2 = {}
    similarUser = FindSimilarUser(userSelectedMovies)
    file2.seek(0)
    for row in normalizedRatingReader:
        if str(row[0]) == str(similarUser):
            tempDict = yaml.load(row[1])
            for movie in tempDict:
                if tempDict[movie] > 0:
                    tempDict2.update({movie : tempDict[movie]})
                
    SortedCollFilteredMovies = sorted(tempDict2, key=tempDict2.__getitem__, reverse=True)

    i = 0
    for movie in SortedCollFilteredMovies:
        if i == 10:
            break
        if movie not in userSelectedMovies:
            i = i + 1
            CollaborativeFilteredMovies.append(movie)


#Finds a similar user based on good ratings for the same movie
#Takes user selected movies as input
#No output
def FindSimilarUser(userSelectedMovies):

    file2.seek(0)
    for row in normalizedRatingReader:
        break
    similarUser = row[0]
    tempDict2 = yaml.load(row[1])
    commonMoviesCount = len(tempDict2.keys() & userSelectedMovies.keys())
    PearCo = PearsonCoefficient(row[0])

    file2.seek(0)
    for row in normalizedRatingReader:
        tempDict2 = yaml.load(row[1])
        tempCount = len(tempDict2.keys() & userSelectedMovies.keys())
        if tempCount > commonMoviesCount:
            tempCo = PearsonCoefficient(row[0])
            if tempCo > PearCo:
                PearCo = tempCo
                similarUser = row[0]
                commonMoviesCount = tempCount

    return similarUser



#Calculates the Pearson Correlatin Coefficient between new user and recorded user
#Takes user ID of recorded user as input
#No output
def PearsonCoefficient(userID):

    file2.seek(0)
    for row in normalizedRatingReader:
        if str(row[0]) == str(userID):
            temp = []
            userRatingArray = []
            user = normalizedUserRatings
            comp = yaml.load(row[1])
            for movie in comp:
                if str(movie) not in normalizedUserRatings:
                    userRatingArray.append(0)
                else:
                    userRatingArray.append(normalizedUserRatings[movie])
                temp.append(yaml.load(row[1])[movie])
            for movie in normalizedUserRatings:
                if str(movie) not in yaml.load(row[1]):
                    userRatingArray.append(normalizedUserRatings[movie])
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
    for movieID in ContentFilteredMovies:
        if str(movieID) not in userSelectedMovies and str(movieID) not in recommendedMovies:
            url = GetUrl(movieID)
            recommendedMovies.update({movieID : url})

    for movieID in CollaborativeFilteredMovies:
        if str(movieID) not in userSelectedMovies and str(movieID) not in recommendedMovies:
            url = GetUrl(movieID)
            recommendedMovies.update({movieID : url})

    return recommendedMovies


run(reloader=True, debug=True)
