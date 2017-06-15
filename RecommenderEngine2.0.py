from bottle import run, get, post, request, redirect
import csv
import urllib.parse
import urllib.request
import bs4
import requests
import numpy as np
import yaml
import ast

#FILES
moviesFileName = 'Movies.csv'
genreCountFileName = 'GenreCount.csv'
normalizedRatingDictionaryFileName = 'NormalizedRatingDictionary.csv'
storedURLFileName = 'URL.csv'

file1 = open(moviesFileName, "rt", encoding="utf-8")
movieReader = csv.reader(file1)

file2 = open(genreCountFileName, "rt", encoding="utf-8")
genreCountReader = csv.reader(file2)

file3 = open(normalizedRatingDictionaryFileName, "rt", encoding="utf-8")
normalizedRatingReader = csv.reader(file3)

file4 = open(storedURLFileName, "rt", encoding="utf-8")
urlReader = csv.reader(file4)



#GLOBAL VARIABLES
global userGenreCounter
userGenreCounter = {'Comedy' : 0, 'Action' : 0, 'Sci-Fi' : 0, 'Drama' : 0, 'Romance' : 0, 'Thriller' : 0, 'Mystery' : 0, 'Horror' : 0, 'Animation' : 0, 'Adventure' : 0}
#For Content Filtering Method

global b
b = [] #Stores the NP Array of user's genre rating

global topUsers
topUsers = [] #Stores list of similar users in decreasing order of Pearson Coefficient with user

global recommendedMoviesDict
recommendedMoviesDict = {} #Stores recommended movies and the IMDb URLs of those movies



#Post request which accepts selected movies and ratings
#Selected movies and ratings in JSON format
#No output
@post('/selectedmovies')
def GetMovieListAndGenreCount():

    global userSelectedMovies
    userSelectedMovies = request.json.get('selectedmovieslist')

    file4.seek(0)

    RatingNormalizer(userSelectedMovies)

    redirect('/recommended')



#Normalizes the user's ratings
#Takes user selected movies as input
#No output
def RatingNormalizer(userSelectedMovies):

    normalizedMovieRatingsDict = {}
    total = 0
    count = 0

    for movie in userSelectedMovies:
        total += userSelectedMovies[movie]
        count = count + 1
    average = total / count

    for movie in userSelectedMovies:
        normalizedMovieRatingsDict.update({str(movie) : userSelectedMovies[movie] - average})

    GenreCounterUpdater(normalizedMovieRatingsDict)



#Updates the genre count based on selected movies and ratings
#Takes selected movies and rating dictionary as input
#No output
def GenreCounterUpdater(normalizedMovieRatingsDict):

    for genre in userGenreCounter:
        userGenreCounter[genre] = 0 #Resetting all genre counts to zero

    normalizedUserGenreRatings = []

    for userMovieID in normalizedMovieRatingsDict:
        file1.seek(0)
        for row in movieReader:
            if str(row[0]) == str(userMovieID):
                for genre in row[2].split('|'):
                    if genre in userGenreCounter:
                        userGenreCounter[genre] += round(normalizedMovieRatingsDict[userMovieID], 2)
                break

    for genre in userGenreCounter:
        normalizedUserGenreRatings.append(userGenreCounter[genre])

    SortUsers(normalizedUserGenreRatings)



#Sorts the stored users based on the cosine angle between the rating vectors of the stored user and new user
#No input
#No output
def SortUsers(normalizedUserGenreRatings):

    pearsonCoefficientDict = {}
    file2.seek(0)
    b = np.array(normalizedUserGenreRatings)

    for row in genreCountReader:
        pearCo = PearsonCoefficient(ast.literal_eval(row[1]), b)
        pearsonCoefficientDict.update({row[0] : pearCo})

    sortedUsers = sorted(pearsonCoefficientDict, key = pearsonCoefficientDict.__getitem__, reverse = True)
    for i in range(0, 5):
        topUsers.append(sortedUsers[i])

    SelectMovies(topUsers)



#Calculates the cosine angle between the stored user's and new user's rating vectors
#Takes rating lists as input
#Returns cosine angle between rating vectors
def PearsonCoefficient(genreCountList, b):

    a = np.array(genreCountList)

    cosine = (np.dot(a, b)) / ((np.sqrt((a * a).sum())) * np.sqrt((b * b).sum()))

    return cosine



#Generates a list of movies with good ratings between all the most similar users
#Takes list of top 5 most similar users
#No output
def SelectMovies(topUsers):

    recommendedMoviesTempDict = {}

    for j in topUsers:
        file3.seek(0)
        for row in normalizedRatingReader:
            if str(row[0]) == str(j):
                tempDict = yaml.load(row[1])
                for i in tempDict:
                    if tempDict[i] > 0:
                        if i not in recommendedMoviesTempDict:
                            recommendedMoviesTempDict.update({i : tempDict[i]})

    recommendedMoviesList = sorted(recommendedMoviesTempDict, key = recommendedMoviesTempDict.__getitem__, reverse = True)

    for i in range(0, 15):
        url = GetUrl(recommendedMoviesList[i])
        recommendedMoviesDict.update({recommendedMoviesList[i] : url})



#Returns the IMDb URL of the movie
#Takes movie ID as input
#Returns URL of the movie
def GetUrl(movieID):

    #file4.seek(0)
    #As the Movie IDs are in ascending order, there is no need to reset the file reader to starting
    url = ""
    for row4 in urlReader:
        if str(movieID) == str(row4[0]):
            url = str(row4[1])
            break
    return url



#Get request to display the recommended movies
#No input
#Returns a dictionary of recommended movies and their IMDb URLs
@get('/recommended')
def GetRecommendedMovies():

    return recommendedMoviesDict



run(reloader=True, debug=True)
