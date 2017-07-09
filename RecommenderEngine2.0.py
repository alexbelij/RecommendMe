from flask import Flask, request, redirect, url_for, jsonify
import csv
import numpy as np
import yaml
import ast

app = Flask(__name__)

#FILES
movies_filename = 'Movies.csv'
genre_count_filename = 'GenreCount.csv'
normalized_rating_dictionary_filename = 'NormalizedRatingDictionary.csv'
stored_URL_filename = 'URL.csv'

file1 = open(movies_filename, "rt", encoding="utf-8")
movie_reader = csv.reader(file1)

file2 = open(genre_count_filename, "rt", encoding="utf-8")
genre_count_reader = csv.reader(file2)

file3 = open(normalized_rating_dictionary_filename, "rt", encoding="utf-8")
normalized_rating_reader = csv.reader(file3)

file4 = open(stored_URL_filename, "rt", encoding="utf-8")
url_reader = csv.reader(file4)



#GLOBAL VARIABLES
user_genre_counter = {'Comedy' : 0, 'Action' : 0, 'Sci-Fi' : 0, 'Drama' : 0, 'Romance' : 0, 'Thriller' : 0, 'Mystery' : 0, 'Horror' : 0, 'Animation' : 0, 'Adventure' : 0}
#For Content Filtering Method

b = [] #Stores the NP Array of user's genre rating

top_users = [] #Stores list of similar users in decreasing order of Pearson Coefficient with user

recommended_movies_dict = {} #Stores recommended movies and the IMDb URLs of those movies



@app.route('/selectedmovies', methods=['POST'])
def GetMovieListAndGenreCount():
    """
    Post request which accepts selected movies and ratings.
    Selected movies and ratings in JSON format.
    No output.
    """
    global user_selected_movies
    user_selected_movies = (request.json)['selectedmovieslist']

    file4.seek(0)

    RatingNormalizer(user_selected_movies)

    return redirect(url_for('GetRecommendedMovies'))


  
def RatingNormalizer(user_selected_movies):
    """
    Normalizes the user's ratings.
    Takes user selected movies as input.
    No output.
    """
    normalized_movies_rating_dict = {}
    total = 0
    count = 0

    for movie in user_selected_movies:
        total += user_selected_movies[movie]
        count = count + 1
    average = total / count

    for movie in user_selected_movies:
        normalized_movies_rating_dict.update({str(movie) : user_selected_movies[movie] - average})

    GenreCounterUpdater(normalized_movies_rating_dict)



def GenreCounterUpdater(normalized_movies_rating_dict):
    """
    Updates the genre count based on selected movies and ratings.
    Takes selected movies and rating dictionary as input.
    No output.
    """
    global user_genre_counter
    for genre in user_genre_counter:
        user_genre_counter[genre] = 0 #Resetting all genre counts to zero

    normalized_user_genre_ratings = []

    for user_movie_ID in normalized_movies_rating_dict:
        file1.seek(0)
        for row in movie_reader:
            if str(row[0]) == str(user_movie_ID):
                for genre in row[2].split('|'):
                    if genre in user_genre_counter:
                        user_genre_counter[genre] += round(normalized_movies_rating_dict[user_movie_ID], 2)
                break

    for genre in user_genre_counter:
        normalized_user_genre_ratings.append(user_genre_counter[genre])

    SortUsers(normalized_user_genre_ratings)



def SortUsers(normalized_user_genre_ratings):
    """
    Sorts the stored users based on the cosine angle between the rating vectors of the stored user and new user.
    No input.
    No output.
    """
    pearson_coefficient_dict = {}
    file2.seek(0)
    b = np.array(normalized_user_genre_ratings)

    for row in genre_count_reader:
        pearCo = PearsonCoefficient(ast.literal_eval(row[1]), b)
        pearson_coefficient_dict.update({row[0] : pearCo})

    sorted_users = sorted(pearson_coefficient_dict, key = pearson_coefficient_dict.__getitem__, reverse = True)
    global top_users
    for i in range(0, 5):
        top_users.append(sorted_users[i])

    SelectMovies(top_users)



def PearsonCoefficient(genre_count_list, b):
    """
    Calculates the cosine angle between the stored user's and new user's rating vectors.
    Takes rating lists as input.
    Returns cosine angle between rating vectors.
    """
    a = np.array(genre_count_list)

    cosine = (np.dot(a, b)) / ((np.sqrt((a * a).sum())) * np.sqrt((b * b).sum()))

    return cosine



def SelectMovies(top_users):
    """
    Generates a list of movies with good ratings between all the most similar users.
    Takes list of top 5 most similar users.
    No output.
    """
    recommended_movies_temp_dict = {}

    for j in top_users:
        file3.seek(0)
        for row in normalized_rating_reader:
            if str(row[0]) == str(j):
                temp_dict = yaml.load(row[1])
                for i in temp_dict:
                    if temp_dict[i] > 0:	#If the normalized rating is greater than 0, the user liked it
                        if i not in recommended_movies_temp_dict:
                            recommended_movies_temp_dict.update({i : temp_dict[i]})

    global recommended_movies_list
    recommended_movies_list = sorted(recommended_movies_temp_dict, key = recommended_movies_temp_dict.__getitem__, reverse = True)

    global recommended_movies_dict
    for i in range(0, 15):
        url = GetUrl(recommended_movies_list[i])
        recommended_movies_dict.update({recommended_movies_list[i] : url})



def GetUrl(movie_ID):
    """
    Returns the IMDb or Rotten Tomatoes URL of the movie.
    Takes movie ID as input.
    Returns URL of the movie.
    """
    #file4.seek(0)
    #As the Movie IDs are in ascending order, there is no need to reset the file reader to starting
    url = ""
    for row4 in url_reader:
        if str(movie_ID) == str(row4[0]):
            url = str(row4[1])
            break
    return url



@app.route('/recommended', methods=['GET'])
def GetRecommendedMovies():
    """
    GET request to display the recommended movies.
    No input.
    Returns a dictionary of recommended movies and their IMDb URLs.
    """
    return jsonify(recommended_movies_dict)



if __name__ == "__main__":
    app.run(debug=True)
