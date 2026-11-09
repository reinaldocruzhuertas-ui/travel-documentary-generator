import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time

# -----------------------------
# Transport Types
# -----------------------------
TRANSPORT_TYPES = {
    "Walking": "🚶", "Bicycle": "🚲", "Motorbike": "🏍️", "Car": "🚗",
    "Bus": "🚌", "Train": "🚆", "Plane": "✈️", "Helicopter": "🚁",
    "Drone": "🛸", "Ship": "🚢", "Boat": "⛵", "Swimming": "🏊",
    "Horse": "🐎", "Camel": "🐪", "Donkey": "🫏"
}

# -----------------------------
# Read trip
# -----------------------------
trip = pd.read_csv("data/trip.csv")

locations = [trip.iloc[0]["From"]]
for _, row in trip.iterrows():
    locations.append(row["To"])

transports = trip["Transport"].tolist()

# -----------------------------
# Geocode
# -----------------------------
geo = Nominatim(user_agent="travel_documentary_generator", timeout=10)

latitudes = []
longitudes = []

print("Getting coordinates...")
for city in locations:
    location = geo.geocode(f"{city} Australia")
    latitudes.append(location.latitude)
    longitudes.append(location.longitude)
    print(f"{city}: {location.latitude}, {location.longitude}")
    time.sleep(1)

# -----------------------------
# Build frames
# -----------------------------
frames = []
steps_per_segment = 50
frame_number = 0

for segment in range(len(locations) - 1):
    start_lat = latitudes[segment]
    start_lon = longitudes[segment]
    end_lat = latitudes[segment + 1]
    end_lon = longitudes[segment + 1]

    transport = transports[segment]
    transport_icon = TRANSPORT_TYPES.get(transport, "❓")

    # Title accumulates all legs so far
    title_lines = []
    for i in range(segment + 1):
        icon = TRANSPORT_TYPES.get(transports[i], "❓")
        title_lines.append(f"{icon} {locations[i]} → {locations[i + 1]}")
    title_text = "<br>".join(title_lines)

    # Completed leg emojis (parked at endpoints)
    completed_lats = [latitudes[i + 1] + (i * 0.03) for i in range(segment)]
    completed_lons = [longitudes[i + 1] + (i * 0.03) for i in range(segment)]
    completed_icons = [
        TRANSPORT_TYPES.get(transports[i], "❓") for i in range(segment)
    ]

    for step in range(steps_per_segment + 1):
        progress = step / steps_per_segment

        current_lat = start_lat + progress * (end_lat - start_lat)
        current_lon = start_lon + progress * (end_lon - start_lon)

        route_lats = latitudes[:segment + 1] + [current_lat]
        route_lons = longitudes[:segment + 1] + [current_lon]
        city_labels = locations[:segment + 1] + [locations[segment + 1]]

        emoji_lats = completed_lats + [current_lat]
        emoji_lons = completed_lons + [current_lon]
        emoji_text = completed_icons + [transport_icon]

        frames.append(
            go.Frame(
                data=[
                    # Trace 0: route line + city markers
                    go.Scattermap(
                        lon=route_lons,
                        lat=route_lats,
                        mode="lines+markers+text",
                        text=city_labels,
                        textposition="top center",
                        line=dict(width=4, color="royalblue"),
                        marker=dict(size=8, color="royalblue"),
                    ),
                    # Trace 1: all emojis
                    go.Scattermap(
                        lon=emoji_lons,
                        lat=emoji_lats,
                        mode="text",
                        text=emoji_text,
                        textfont=dict(size=28),
                    ),
                ],
                layout=go.Layout(title=title_text),
                name=str(frame_number),
            )
        )
        frame_number += 1

# -----------------------------
# Initial figure
# -----------------------------
initial_icon = TRANSPORT_TYPES.get(transports[0], "❓")
initial_title = ""

fig = go.Figure(
    data=[
        go.Scattermap(
            lon=[longitudes[0]],
            lat=[latitudes[0]],
            mode="lines+markers+text",
            text=[locations[0]],
            textposition="top center",
            line=dict(width=4, color="royalblue"),
            marker=dict(size=8, color="royalblue"),
        ),
        go.Scattermap(
            lon=[longitudes[0]],
            lat=[latitudes[0]],
            mode="text",
            text=[initial_icon],
            textfont=dict(size=28),
        ),
    ],
    frames=frames,
)

# -----------------------------
# Layout
# -----------------------------
fig.update_layout(
    autosize=True,
    margin=dict(l=0, r=0, t=160, b=0),

    title=dict(
        text=initial_title,
        x=0.02,
        y=0.99,
        xanchor="left",
        yanchor="top",
        font=dict(size=11),
    ),

    map=dict(
        style="outdoors",          # terrain + rivers, no token needed
        # fitbounds defaults to "locations", auto-frames route points
    ),

    updatemenus=[
        dict(
            type="buttons",
            x=0.02,
            y=0.75,
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": 100, "redraw": True},
                            "fromcurrent": True,
                        },
                    ],
                )
            ],
        )
    ],
)

fig.show(config={"responsive": True, "displayModeBar": False})