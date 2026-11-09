import json
import os
import webbrowser

# ============================================================
# 1. Define the Sydney to Melbourne Train Route
# ============================================================
# Realistic coordinates matching the railway line
ROUTE = [
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Campbelltown", "lat": -34.0667, "lon": 150.8167},
    {"name": "Goulburn", "lat": -34.7550, "lon": 149.7186},
    {"name": "Wagga Wagga", "lat": -35.1082, "lon": 147.3598},
    {"name": "Albury", "lat": -36.0806, "lon": 146.9161},
    {"name": "Seymour", "lat": -37.0264, "lon": 145.1361},
    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631},
]

# 2. Generate animation frames for the camera and train
frames = []
STEPS_PER_LEG = 100 # Higher = smoother animation

for i in range(len(ROUTE) - 1):
    start = ROUTE[i]
    end = ROUTE[i + 1]
    
    for step in range(STEPS_PER_LEG):
        p = step / STEPS_PER_LEG
        cur_lat = start["lat"] + p * (end["lat"] - start["lat"])
        cur_lon = start["lon"] + p * (end["lon"] - start["lon"])
        
        frames.append({
            "lat": cur_lat,
            "lon": cur_lon,
            # Add a nice 3D tilt and zoom for the train tracking
            "pitch": 55, 
            "zoom": 8,
            "name": f"Approaching {end['name']}"
        })

# Add the final destination frame
frames.append({
    "lat": ROUTE[-1]["lat"],
    "lon": ROUTE[-1]["lon"],
    "pitch": 55,
    "zoom": 8,
    "name": "Arrived at Melbourne"
})

# Convert route and frames to JSON for the JavaScript
route_coords = [[c["lon"], c["lat"]] for c in ROUTE]
frames_json = json.dumps(frames)
route_json = json.dumps(route_coords)

# ============================================================
# 3. The MapLibre HTML/JS Template
# ============================================================
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sydney to Melbourne Train Journey</title>
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        #ui-overlay {{
            position: absolute; top: 20px; left: 20px; z-index: 10;
            background: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); width: 250px;
        }}
        h1 {{ margin: 0 0 10px 0; font-size: 18px; color: #333; }}
        button {{
            width: 100%; padding: 10px; background: #0055ff; color: white; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;
        }}
        button:hover {{ background: #0044cc; }}
        .status {{ margin-top: 10px; font-size: 14px; color: #555; font-weight: bold; }}
        .train-emoji {{
            font-size: 45px;
            filter: drop-shadow(0px 10px 5px rgba(0,0,0,0.5));
            transition: transform 0.1s linear;
        }}
    </style>
</head>
<body>
    <div id="ui-overlay">
        <h1>Sydney → Melbourne</h1>
        <button id="play-btn" onclick="startAnimation()">▶ Play Journey</button>
        <div class="status" id="status-text">Ready to depart</div>
    </div>
    <div id="map"></div>
    <script>
        // Initialize MapLibre
        const map = new maplibregl.Map({{
            container: 'map',
            style: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
            center: [{route_coords[0][0]}, {route_coords[0][1]}],
            zoom: 7,
            pitch: 55,
            bearing: 0,
            antialias: true
        }});

        map.on('load', () => {{
            // 1. Add 3D Terrain
            map.addSource('terrain', {{
                type: 'raster-dem',
                url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json',
                tileSize: 256
            }});
            map.setTerrain({{ source: 'terrain', exaggeration: 1.5 }});
            
            // 2. Add the full route line (grey, to show where we are going)
            map.addSource('route', {{
                type: 'geojson',
                data: {{
                    type: 'Feature',
                    geometry: {{ type: 'LineString', coordinates: {route_json} }}
                }}
            }});
            map.addLayer({{
                id: 'route-bg',
                type: 'line',
                source: 'route',
                layout: {{ 'line-join': 'round', 'line-cap': 'round' }},
                paint: {{ 'line-color': '#aaaaaa', 'line-width': 3, 'line-dasharray': [2, 2] }}
            }});

            // 3. Add the active tracking line (blue)
            map.addSource('active-route', {{
                type: 'geojson',
                data: {{ type: 'Feature', geometry: {{ type: 'LineString', coordinates: [] }} }}
            }});
            map.addLayer({{
                id: 'active-route',
                type: 'line',
                source: 'active-route',
                layout: {{ 'line-join': 'round', 'line-cap': 'round' }},
                paint: {{ 'line-color': '#0055ff', 'line-width': 5 }}
            }});

            // 4. Add the moving train emoji
            const el = document.createElement('div');
            el.className = 'train-emoji';
            el.innerText = '🚆';
            
            const marker = new maplibregl.Marker({{ element: el, anchor: 'center' }})
                .setLngLat([{route_coords[0][0]}, {route_coords[0][1]}])
                .addTo(map);

            // 5. Animation Data
            const frames = {frames_json};
            let animationInterval = null;
            let currentFrame = 0;
            let activeCoordinates = [[{route_coords[0][0]}, {route_coords[0][1]}]];

            window.startAnimation = function() {{
                if (animationInterval) clearInterval(animationInterval);
                currentFrame = 0;
                activeCoordinates = [[{route_coords[0][0]}, {route_coords[0][1]}]];

                document.getElementById('play-btn').innerText = "🚆 Traveling...";
                document.getElementById('play-btn').disabled = true;

                animationInterval = setInterval(() => {{
                    if (currentFrame >= frames.length) {{
                        clearInterval(animationInterval);
                        document.getElementById('play-btn').innerText = "🏁 Arrived";
                        document.getElementById('status-text').innerText = "Welcome to Melbourne!";
                        return;
                    }}

                    const frame = frames[currentFrame];

                    // Update train position
                    marker.setLngLat([frame.lon, frame.lat]);

                    // Update the blue line tracing behind the train
                    activeCoordinates.push([frame.lon, frame.lat]);
                    map.getSource('active-route').setData({{
                        type: 'Feature',
                        geometry: {{ type: 'LineString', coordinates: activeCoordinates }}
                    }});

                    // Smoothly fly the camera to follow the train
                    map.jumpTo({{
                        center: [frame.lon, frame.lat],
                        pitch: frame.pitch,
                        zoom: frame.zoom,
                        bearing: 0
                    }});

                    document.getElementById('status-text').innerText = frame.name;
                    currentFrame++;

                }}, 50); // 50ms = 20 frames per second
            }};
        }});
    </script>
</body>
</html>
"""

# ============================================================
# 4. Save and open the file
# ============================================================
output_file = "sydney_melbourne_train.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Success! Generated {output_file}")
print("Opening in your default browser...")

# Automatically open in browser
file_path = "file://" + os.path.abspath(output_file)
webbrowser.open(file_path)