from flask import Flask, request, redirect
import json
import pymysql
import ast
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

db = pymysql.connect(host="localhost", user="root", passwd="shamanmb", db="MovieDB")
cur = db.cursor()

GENRES = ['all', 'action', 'adventure', 'animation', 'comedy', 'drama', 'horror', 'mystery', 'romance', 'sci-fi', 'thriller']



@app.route("/genres") # Done
def genres():
    """
    In GET request, the genres are sent back to the user.
    """
    if request.method == 'GET':
        genres = {'genres' : GENRES}
        response = app.response_class(
            response=json.dumps(genres),
            status=200,
            mimetype='application/json'
        )
        return response



@app.route("/movies") # Done
def movies():
    """
    In GET request:
        - It takes genre argument.
        - Default value is 'all'.
        - Returns a list of movies belonging to that genre.
    """
    if request.method == 'GET':
        genre = request.args.get('genre', None)
        if genre == None:
            response = app.response_class(
                response=json.dumps({'Error' : 'Missing arguments - genre'}),
                status=200,
                mimetype='application/json'
            )
            return response
        limit = request.args.get('limit', 100)
        genre = genre.lower()
        if genre not in GENRES:
            response = app.response_class(
                response=json.dumps({'Error' : 'Invalid genre'}),
                status=200,
                mimetype='application/json'
            )
            return response
        else:
            if genre == 'all':
                genre = ''
            cur.execute("SELECT * FROM movies WHERE genres LIKE \'%{}%\' LIMIT {}".format(genre, limit))
            movies = []
            for movie in cur.fetchall():
                genres = []
                for genre in movie[2].split("|"):
                    if genre.lower() in GENRES:
                        genres.append(genre.lower())
                movies.append({'ID' : movie[0], 'Title' : str(movie[1])[:-7], 'Year' : str(movie[1][-5:-1]), 'Genres' : genres})
            movie_dict = {'movies' : movies}
            response = app.response_class(
                response=json.dumps(movie_dict),
                status=200,
                mimetype='application/json'
            )
            return response



@app.route("/details")
def return_details():
    """
    """
    if request.method == 'GET':
        movie_id = request.args.get('ID', None)
        if movie_id == None:
            response = app.response_class(
                response=json.dumps({'Error' : 'Missing parameter - ID'}),
                status=200,
                mimetype='application/json'
            )
            return response
        done = cur.execute("SELECT * FROM movies WHERE movie_id = {}".format(movie_id))
        if done == 0:
            response = app.response_class(
                response=json.dumps({'Error' : 'Invalid movie ID'}),
                status=200,
                mimetype='application/json'
            )
            return response
        else:
            movie = cur.fetchone()
            movie_id = movie[0]
            title = movie[1][:-7]
            year = movie[1][-5:-1]
            genres = [i.lower() for i in movie[2].split("|") if i.lower() in GENRES]
            details = {'ID' : movie_id, 'Title' : title, 'Year' : year, 'Genres' : genres}
            response = app.response_class(
                response=json.dumps({'Details' : details}),
                status=200,
                mimetype='application/json'
            )
            return response



@app.route("/recommend", methods = ['POST'])
def accept_data():
    """
    In POST request
        - Accepts data from user.
        - In the format - {"<Movie ID 1>" : <Rating 1>, "<Movie ID 2>" : <Rating 2>, ...}
    """
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type', None)
        if content_type != "application/json":
            response = app.response_class(
                response=json.dumps({'Error' : 'Invalid content type'}),
                status=200,
                mimetype='application/json'
            )
            return response
        data = (request.data).decode("utf-8")
        try:
            data = ast.literal_eval(data)
        except:
            response = app.response_class(
                response=json.dumps({'Error' : 'Invalid content type'}),
                status=200,
                mimetype='application/json'
            )
            return response
        total_rating = 0
        n = 0

        for i in data:
            movie_id = i
            rating = data[i]

            # Checking if the rating is a valid rating.
            if rating < 1 or rating > 5:
                response = app.response_class(
                    response=json.dumps({'Error' : 'Rating out of bounds'}),
                    status=200,
                    mimetype='application/json'
                )
                return response
            total_rating += rating
            n += 1

            # Checking if the movie ID is a valid ID.
            valid = cur.execute("SELECT * FROM movies WHERE movie_id = {}".format(movie_id))
            if valid == 0:
                response = app.response_class(
                    response=json.dumps({'Error' : 'Invalid movie ID'}),
                    status=200,
                    mimetype='application/json'
                )
                return response

        normalized_rating = normalize(data, total_rating/n)

        # Getting value of each genre
        normalized_user_genre_counter = genre_count(normalized_rating)
        user_genre_counter = normal_genre_count(data)

        content_filtered_movies = content_filtering(user_genre_counter)

        movie_details = get_details(content_filtered_movies)

        response = app.response_class(
        response=json.dumps({'Content Filtered Movies' : movie_details}),
        status=200,
        mimetype='application/json'
        )
        return response

def get_details(movie_list): # Done
    """
    Returns the details of all the movies in the list.
    """
    movie_details = []
    cur.execute("SELECT * FROM movies WHERE movie_id in ({})".format(",".join([str(i) for i in movie_list])))
    for movie in cur.fetchall():
        movie_id = movie[0]
        title = movie[1][:-7]
        year = movie[1][-5:-1]
        genres = [i.lower() for i in movie[2].split("|") if i.lower() in GENRES]
        details = {'ID' : movie_id, 'Title' : title, 'Year' : year, 'Genres' : genres}
        movie_details.append(details)
    return movie_details



def content_filtering(user_genre_counter): # Done
    """
    Returns a list of the top 10 movies which might receieve the best rating from the user based on genres.
    """
    unwatched_movie_ratings = {}
    cur.execute("SELECT movie_id, genres FROM movies")
    for movie in cur.fetchall():
        movie_id = movie[0]
        genres = [i.lower() for i in (movie[1]).split("|")]
        value = 0
        for genre in genres:
            if genre in GENRES:
                value += user_genre_counter[genre]
        unwatched_movie_ratings.update({movie_id : value})
    sorted_unwatched_movies = sorted(unwatched_movie_ratings, key=unwatched_movie_ratings.get, reverse=True)
    return sorted_unwatched_movies[:10]



def normal_genre_count(data): # Done
    """
    Returns a dictionary of genres with their complete ratings.
    """
    genre_rating = {'comedy' : 0, 'action' : 0, 'sci-fi' : 0, 'drama' : 0, 'romance' : 0, 'thriller' : 0, 'mystery' : 0, 'horror' : 0, 'animation' : 0, 'adventure' : 0}
    for movie_id in data:
        cur.execute("SELECT genres FROM movies WHERE movie_id = {}".format(movie_id))
        genres = (cur.fetchone()[0]).split("|")

        for genre in genres:
            if genre.lower() in genre_rating:
                genre_rating[genre.lower()] += data[movie_id]

    return genre_rating



def genre_count(normalized_rating):
    """
    Returns a dictionary of values of normalized ratings for each genre.
    """
    normalized_user_genre_counter =  {'comedy' : 0, 'action' : 0, 'sci-fi' : 0, 'drama' : 0, 'romance' : 0, 'thriller' : 0, 'mystery' : 0, 'horror' : 0, 'animation' : 0, 'adventure' : 0}
    for movie_id in normalized_rating:
        cur.execute("SELECT genres FROM movies WHERE movie_id = {}".format(movie_id))
        genres = cur.fetchone()[0]
        genres = genres.split("|")

        for genre in genres:
            # Removing unnecessary genres
            if genre.lower() in normalized_user_genre_counter:
                normalized_user_genre_counter[genre.lower()] += round(normalized_rating[movie_id], 2)

    return normalized_user_genre_counter



def normalize(ratings_dict, average): # Done
    """
    Returns the normalized ratings of the user.
    """
    normalized_dict = {}
    for i in ratings_dict:
        normalized_dict.update({i : ratings_dict[i] - average})
    return normalized_dict



if __name__ == '__main__':
    app.run(port=5000, debug=True)
