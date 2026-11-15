import requests
import json

# Bogota -> Tunja
url = (
    "https://router.project-osrm.org/"
    "route/v1/driving/"
    "-74.0721,4.7110;"
    "-73.3678,5.5353"
    "?overview=full&geometries=geojson"
)

response = requests.get(url)
data = response.json()

coordinates = data["routes"][0]["geometry"]["coordinates"]

html = f"""
<!DOCTYPE html>
<html>
<head>

<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css"
      rel="stylesheet" />

<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js">
</script>

<style>
html, body {{
    margin:0;
    padding:0;
    width:100%;
    height:100%;
}}

#map {{
    width:100%;
    height:100%;
}}
</style>

</head>

<body>

<div id="map"></div>

<script>

const routeCoordinates =
{json.dumps(coordinates)};

const map = new maplibregl.Map({{
    container: 'map',

    style: {{
        version: 8,
        sources: {{}},
        layers: []
    }},

    center: routeCoordinates[0],
    zoom: 8
}});

map.on('load', () => {{

    // Route Source
    map.addSource('route', {{
        type: 'geojson',
        data: {{
            type: 'Feature',
            geometry: {{
                type: 'LineString',
                coordinates: routeCoordinates
            }}
        }}
    }});

    // Route Layer
    map.addLayer({{
        id: 'route',
        type: 'line',
        source: 'route',
        paint: {{
            'line-color': '#0000FF',
            'line-width': 5
        }}
    }});

    // First coordinate
    const start = routeCoordinates[0];

    // Last coordinate
    const end = routeCoordinates[routeCoordinates.length - 1];

    // Green Start Marker
    new maplibregl.Marker({{
        color: 'green'
    }})
    .setLngLat(start)
    .setPopup(
        new maplibregl.Popup()
            .setHTML('<b>Bogotá</b>')
    )
    .addTo(map);

    // Red End Marker
    new maplibregl.Marker({{
        color: 'red'
    }})
    .setLngLat(end)
    .setPopup(
        new maplibregl.Popup()
            .setHTML('<b>Tunja</b>')
    )
    .addTo(map);

    // Auto zoom to route
    const bounds = new maplibregl.LngLatBounds();

    routeCoordinates.forEach(coord => {{
        bounds.extend(coord);
    }});

    map.fitBounds(bounds, {{
        padding: 50
    }});

}});

</script>

</body>
</html>
"""

with open("route_maplibre.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Created route_maplibre.html")