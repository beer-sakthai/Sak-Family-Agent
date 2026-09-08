import urllib.request
import json
req = urllib.request.Request("http://localhost:8000/submit", data=json.dumps({"event":"completed","pr_url":""}).encode("utf-8"), headers={"Content-Type": "application/json"})
urllib.request.urlopen(req)
