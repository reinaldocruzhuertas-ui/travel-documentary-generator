from keplergl import KeplerGl
import json

# 1. Define your route (using 3 cities as an example)
# Kepler.gl's Trip Layer requires coordinates with a timestamp (Unix seconds)
cities = [
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Canberra", "lat": -35.2809, "lon": 149.1300},
    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631},
]

# 2. Build GeoJSON data with timestamps
# Simulate 1 hour between each city (3600 seconds)
coordinates = []
base_time = 1564184363  # An arbitrary start time

for i, city in enumerate(cities):
    # Altitude is set to 0, timestamp increases by 3600 seconds per city
    timestamp = base_time + (i * 3600)
    coordinates.append([city["lon"], city["lat"], 0, timestamp])

trip_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "My Journey"},
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        }
    ]
}

# 3. Create a Kepler.gl map
# 'data' dictionary key 'trips' will be the dataId of the layer
map_1 = KeplerGl(height=600, data={'trips': trip_geojson})

# 4. Export as standalone HTML
# center_map=True will automatically zoom to fit your data
map_1.save_to_html(file_name='kepler_journey.html', center_map=True)

print("Success! Open 'kepler_journey.html' in your browser.")
print("You should see an animated path with a fading tail.")