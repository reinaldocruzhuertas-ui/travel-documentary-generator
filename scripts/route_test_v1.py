import requests
import folium

url = (
    "https://router.project-osrm.org/"
    "route/v1/driving/"
    "-74.0721,4.7110;"
    "-73.3678,5.5353"
    "?overview=full&geometries=geojson"
)

data = requests.get(url).json()

coords = data["routes"][0]["geometry"]["coordinates"]

# OSRM returns [lon, lat]
route_points = [[lat, lon] for lon, lat in coords]

m = folium.Map(
    location=[4.7110, -74.0721],
    zoom_start=8
)

folium.PolyLine(
    route_points,
    color="blue",
    weight=5
).add_to(m)

m.save("route.html")

print("Map saved as route.html")