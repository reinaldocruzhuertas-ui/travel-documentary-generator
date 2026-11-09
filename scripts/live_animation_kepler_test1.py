from keplergl import KeplerGl

# 1. Define the Train trip
# (I added a slight curve to the coordinates so it doesn't look like a laser beam)
# Format: [Longitude, Latitude, Altitude, Timestamp]
coordinates = [
    [151.2093, -33.8688, 0, 1698768000], # Sydney
    [150.8000, -34.2000, 0, 1698768600], # Campbelltown-ish
    [150.2000, -34.6000, 0, 1698769200], # Southern Highlands
    [149.8000, -34.9000, 0, 1698769800], # Goulburn
    [149.1300, -35.2809, 0, 1698770400]  # Canberra
]

# 2. Format as GeoJSON
trip_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Sydney to Canberra Train"},
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        }
    ]
}

# 3. Create the map
map_1 = KeplerGl(height=800, data={'Train_Trip': trip_geojson})

# 4. Pre-configure the map so it auto-loads perfectly
config = {
    "version": "v1",
    "config": {
        "mapStyle": {
            "styleType": "voyager"  # <--- Sets Voyager automatically
        },
        "visState": {
            "layers": [
                {
                    "id": "train_layer",
                    "type": "trip",
                    "config": {
                        "dataId": "Train_Trip",
                        "label": "Train Journey",
                        "color": [0, 105, 205], # Blue
                        "columns": {
                            "lat": "lat", "lng": "lng", "altitude": "altitude", "time": "time"
                        },
                        "isVisible": True,
                        "visConfig": {
                            "trailLength": 30,   # Long trail
                            "opacity": 1,
                            "thickness": 5,
                        }
                    }
                }
            ]
        }
    }
}

map_1.config = config
map_1.save_to_html(file_name='kepler_train.html', center_map=True)

print("Success! Open 'kepler_train.html' in Chrome.")