import csv
import urllib.parse
import urllib.request
import bs4
import requests

file2 = open("Movies.csv", "rt", encoding="utf-8")
file3 = open("URL.csv", "wt", encoding="utf-8", newline='')
movieReader = csv.reader(file2)

URLWriter = csv.writer(file3)

file2.seek(0)
for row in movieReader:
    try:
        movieSearchTerm = row[1] + " imdb"
        SearchUrl = r'https://www.google.co.in/search?q=' + urllib.parse.quote_plus(movieSearchTerm)
        searchResult = requests.get(SearchUrl)
        searchResult.raise_for_status()
        soup = bs4.BeautifulSoup(searchResult.text, 'html.parser')
        IMDbID = str(soup.find('cite'))[32:41]
        url = "http://www.imdb.com/title/" + IMDbID
        URLWriter.writerow((row[0], url))
        print(str(row[0]) + " done")
    except:
        print(str(row[0]) + "error")
        URLWriter.writerow((row[0], "Error"))
