import csv
import urllib.parse
import urllib.request
import bs4
import requests

file2 = open("Movies.csv", "rt", encoding="utf-8")
file3 = open("URL.csv", "wt", encoding="utf-8", newline='')
movie_reader = csv.reader(file2)

URL_writer = csv.writer(file3)

file2.seek(0)
for row in movie_reader:
    try:
        movie_search_term = row[1] + " imdb"
        earch_url = r'https://www.google.co.in/search?q=' + urllib.parse.quote_plus(movieSearchTerm)
        search_result = requests.get(search_url)
        search_result.raise_for_status()
        soup = bs4.BeautifulSoup(search_result.text, 'html.parser')
        imdb_ID = str(soup.find('cite'))[32:41]
        url = "http://www.imdb.com/title/" + imdb_ID
        URL_writer.writerow((row[0], url))
        print(str(row[0]) + " done")
    except:
        print(str(row[0]) + "error")
        URL_writer.writerow((row[0], "Error"))
