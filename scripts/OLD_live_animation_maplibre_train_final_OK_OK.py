import json
import math
import os
import webbrowser
from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# ============================================================
# 1. Read and Geocode Trip Data
# ============================================================
CSV_FILE = Path("data/trip.csv")
GEOCODE_CACHE = Path("data/geocode_cache.csv")

TRANSPORT_TYPES = {
    "Walking": "🚶", "Bicycle": "🚲", "Motorbike": "🏍️", "Car": "🚗",
    "Bus": "🚌", "Train": "🚆", "Plane": "✈️", "Helicopter": "🚁",
    "Drone": "🛸", "Ship": "🚢", "Boat": "⛵", "Swimming": "🏊",
    "Horse": "🐎", "Camel": "🐪", "Donkey": "🫏",
}

def geocode_locations(locations):
    cache = {}
    if GEOCODE_CACHE.exists():
        cached = pd.read_csv(GEOCODE_CACHE)
        for _, row in cached.iterrows():
            cache[str(row["location"])] = (float(row["latitude"]), float(row["longitude"]))

    geo = Nominatim(user_agent="maplibre_travel_app", timeout=20)
    geocode = RateLimiter(geo.geocode, min_delay_seconds=1.1, return_value_on_exception=None)

    coords = []
    for place in locations:
        if place in cache:
            coords.append(cache[place])
        else:
            res = geocode(place, exactly_one=True)
            if not res:
                raise ValueError(f"Could not find {place}")
            coords.append((res.latitude, res.longitude))
            cache[place] = (res.latitude, res.longitude)
            
    pd.DataFrame([{"location": k, "latitude": v[0], "longitude": v[1]} for k, v in cache.items()]).to_csv(GEOCODE_CACHE, index=False)
    return coords

def great_circle_interpolate(start_lat, start_lon, end_lat, end_lon, fraction):
    if fraction <= 0: return start_lat, start_lon
    if fraction >= 1: return end_lat, end_lon

    delta_lon = end_lon - start_lon
    while delta_lon > 180: delta_lon -= 360
    while delta_lon < -180: delta_lon += 360
    adjusted_end_lon = start_lon + delta_lon

    lat1, lon1 = map(math.radians, (start_lat, start_lon))
    lat2, lon2 = map(math.radians, (end_lat, adjusted_end_lon))
    
    def to_vec(lat, lon): return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))
    a, b = to_vec(lat1, lon1), to_vec(lat2, lon2)
    
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    omega = math.acos(dot)

    if abs(omega) < 1e-10: return start_lat, start_lon
    sin_omega = math.sin(omega)
    if abs(sin_omega) < 1e-10: return start_lat + fraction * (end_lat - start_lat), start_lon + fraction * delta_lon

    wa = math.sin((1 - fraction) * omega) / sin_omega
    wb = math.sin(fraction * omega) / sin_omega
    
    x = wa * a[0] + wb * b[0]
    y = wa * a[1] + wb * b[1]
    z = wa * a[2] + wb * b[2]

    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    
    # We standardize longitude back to -180 to 180 for MapLibre compatibility
    lon = start_lon + fraction * (adjusted_end_lon - start_lon)
    while lon > 180: lon -= 360
    while lon < -180: lon += 360

    return lat, lon

# ============================================================
# 2. Build Animation Frames
# ============================================================
trip = pd.read_csv(CSV_FILE)
locations = [str(trip.iloc[0]["From"])] + [str(row["To"]) for _, row in trip.iterrows()]
transports = trip["Transport"].astype(str).tolist()

coords = geocode_locations(locations)
lats = [c[0] for c in coords]
lons = [c[1] for c in coords]

frames = []
STEPS_PER_SEGMENT = 100

for segment in range(len(locations) - 1):
    start_lat, start_lon = lats[segment], lons[segment]
    end_lat, end_lon = lats[segment + 1], lons[segment + 1]
    
    transport = transports[segment].strip().capitalize()
    icon = TRANSPORT_TYPES.get(transport, "❓")
    
    for step in range(STEPS_PER_SEGMENT + 1):
        p = step / STEPS_PER_SEGMENT
        
        if transport == "Plane":
            cur_lat, cur_lon = great_circle_interpolate(start_lat, start_lon, end_lat, end_lon, p)
            zoom = 3 
            pitch = 0 
        elif transport == "Ship":
            cur_lat = start_lat + p * (end_lat - start_lat)
            cur_lon = start_lon + p * (end_lon - start_lon)
            zoom = 6
            pitch = 0 
        else:
            cur_lat = start_lat + p * (end_lat - start_lat)
            cur_lon = start_lon + p * (end_lon - start_lon)
            zoom = 9
            pitch = 55 
            
        frames.append({
            "lat": cur_lat, "lon": cur_lon, "icon": icon, 
            "zoom": zoom, "pitch": pitch,
            "status": f"Traveling to {locations[segment+1]} via {transport}"
        })

frames_json = json.dumps(frames)
route_coords = [[lon, lat] for lat, lon in coords]

# ============================================================
# 3. Generate HTML
# ============================================================
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cinematic World Journey</title>
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        #ui-overlay {{
            position: absolute; top: 20px; left: 20px; z-index: 10;
            background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); width: 250px;
        }}
        h1 {{ margin: 0 0 10px 0; font-size: 18px; color: #333; }}
        button {{
            width: 100%; padding: 10px; background: #0055ff; color: white; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;
            margin-bottom: 5px;
        }}
        button:hover {{ background: #0044cc; }}
        button:disabled {{ background: #88bbff; cursor: not-allowed; }}
        .status {{ margin-top: 5px; font-size: 14px; color: #555; font-weight: bold; }}
        .transport-emoji {{
            font-size: 45px;
            filter: drop-shadow(0px 10px 5px rgba(0,0,0,0.5));
            transition: transform 0.1s linear;
        }}
    </style>
</head>
<body>
    <div id="ui-overlay">
        <h1>World Journey</h1>
        <button id="play-btn" onclick="startAnimation()">▶ Play Journey</button>
        <button id="replay-btn" onclick="startAnimation()" style="display: none;">↺ Replay Journey</button>
        <div class="status" id="status-text">Ready to depart</div>
    </div>
    <div id="map"></div>
    <script>
        const map = new maplibregl.Map({{
            container: 'map',
            style: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
            center: [{route_coords[0][0]}, {route_coords[0][1]}],
            zoom: 5, pitch: 0, bearing: 0, antialias: true
        }});

        map.on('load', () => {{
            map.addSource('terrain', {{
                type: 'raster-dem', url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json', tileSize: 256
            }});
            map.setTerrain({{ source: 'terrain', exaggeration: 1.5 }});
            
            map.addSource('active-route', {{
                type: 'geojson', data: {{ type: 'Feature', geometry: {{ type: 'LineString', coordinates: [] }} }}
            }});
            map.addLayer({{
                id: 'active-route', type: 'line', source: 'active-route',
                layout: {{ 'line-join': 'round', 'line-cap': 'round' }},
                paint: {{ 'line-color': '#0055ff', 'line-width': 5 }}
            }});

            const el = document.createElement('div');
            el.className = 'transport-emoji';
            el.innerText = '🚗';
            
            const marker = new maplibregl.Marker({{ element: el, anchor: 'center' }})
                .setLngLat([{route_coords[0][0]}, {route_coords[0][1]}])
                .addTo(map);

            const frames = {frames_json};
            let animationInterval = null;
            let currentFrame = 0;
            
            // We will store arrays of coordinates (segments separated by the Date Line)
            let segments = [[[{route_coords[0][0]}, {route_coords[0][1]}]]];

            window.startAnimation = function() {{
                if (animationInterval) clearInterval(animationInterval);
                currentFrame = 0;
                segments = [[[{route_coords[0][0]}, {route_coords[0][1]}]]];

                document.getElementById('play-btn').style.display = 'none';
                document.getElementById('replay-btn').style.display = 'none';
                document.getElementById('status-text').innerText = "Preparing...";

                animationInterval = setInterval(() => {{
                    if (currentFrame >= frames.length) {{
                        clearInterval(animationInterval);
                        document.getElementById('replay-btn').style.display = 'block';
                        document.getElementById('replay-btn').innerText = "↺ Replay Journey";
                        document.getElementById('status-text').innerText = "Journey Complete!";
                        return;
                    }}

                    const frame = frames[currentFrame];
                    marker.setLngLat([frame.lon, frame.lat]);
                    el.innerText = frame.icon;

                    // --- THE CLEVER DATE LINE FIX ---
                    const currentSegment = segments[segments.length - 1];
                    const lastCoord = currentSegment[currentSegment.length - 1];
                    const newCoord = [frame.lon, frame.lat];

                    // If the jump in longitude is greater than 180, we crossed the Date Line
                    if (Math.abs(newCoord[0] - lastCoord[0]) > 180) {{
                        // Start a new line segment
                        segments.push([newCoord]);
                    }} else {{
                        // Add to the current line segment
                        currentSegment.push(newCoord);
                    }}

                    map.getSource('active-route').setData({{
                        type: 'FeatureCollection',
                        features: segments.map(seg => ({{
                            type: 'Feature',
                            geometry: {{ type: 'LineString', coordinates: seg }}
                        }}))
                    }});

                    map.jumpTo({{
                        center: [frame.lon, frame.lat],
                        pitch: frame.pitch,
                        zoom: frame.zoom,
                        bearing: 0
                    }});

                    document.getElementById('status-text').innerText = frame.status;
                    currentFrame++;

                }}, 40); 
            }};
        }});
    </script>
</body>
</html>
"""

output_file = "world_journey.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Success! Generated {output_file}")
webbrowser.open("file://" + os.path.abspath(output_file))