import requests
import json

head = {"Content-Type" : "application/json"}

data = {"12" : 2, "15" : 3}

a = requests.post(url="http://127.0.0.1:5000/recommend", json=data)
a = json.loads(a.text)

for i in a["Content Filtered Movies"]:
    print(i["ID"])
