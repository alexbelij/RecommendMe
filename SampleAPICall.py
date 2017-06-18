import requests
import urllib.request

header = '56ed8666' #example ngrok tunnel

baseURL = 'http://{0}.ngrok.io/selectedmovies'.format(header)

payload = {"selectedmovieslist" : {"1" : 4, "2" : 3, "32" : 3, "44" : 1.5, "47" : 4.5, "147" : 3.5, "216" : 2.5, "288" : 2.5, "344" : 4.5}}

requests.post((baseURL), data = payload)

response = urllib.request.urlopen("http://" + header + ".ngrok.io/recommended").read()

print(response)
