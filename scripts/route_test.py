import requests
import json

url = (
    "https://router.project-osrm.org/"
    "route/v1/driving/"
    "-74.0721,4.7110;"
    "-73.3678,5.5353"
    "?overview=full&geometries=geojson"
)

data = requests.get(url).json()

# print(data)

print(json.dumps(data, indent=4))