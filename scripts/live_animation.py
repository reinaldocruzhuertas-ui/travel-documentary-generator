import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time

# -----------------------------
# Create the Dictionary
# Default Transport Types
# ----------------------------

TRANSPORT_TYPES = {
    "Walking": "🚶",
    "Bicycle": "🚲",
    "Motorbike": "🏍️",
    "Car": "🚗",
    "Bus": "🚌",
    "Train": "🚆",
    "Plane": "✈️",
    "Helicopter": "🚁",
    "Drone": "🛸",
    "Ship": "🚢",
    "Boat": "⛵",
    "Swimming": "🏊",
    "Horse": "🐎",
    "Camel": "🐪",
    "Donkey": "🫏"
}




# -----------------------------
# Read trip
# -----------------------------

trip = pd.read_csv("data/trip.csv")

transports = trip["Transport"].tolist()

locations = [trip.iloc[0]["From"]]

for _, row in trip.iterrows():
    locations.append(row["To"])

# -----------------------------
# Geocode
# -----------------------------

geo = Nominatim(
    user_agent="travel_documentary_generator",
    timeout=10
)

latitudes = []
longitudes = []

print("Getting coordinates...")

for city in locations:

    location = geo.geocode(f"{city} Australia")

    latitudes.append(location.latitude)
    longitudes.append(location.longitude)

    print(
        f"{city}: "
        f"{location.latitude}, "
        f"{location.longitude}"
    )

    time.sleep(1)

# -----------------------------
# Calculate map bounds
# -----------------------------

padding_lat = 1
padding_lon = 1

min_lat = min(latitudes) - padding_lat
max_lat = max(latitudes) + padding_lat

min_lon = min(longitudes) - padding_lon
max_lon = max(longitudes) + padding_lon

# -----------------------------
# Create animation frames
# -----------------------------

frames = []

steps_per_segment = 50

frame_number = 0

for segment in range(len(locations) - 1):

    start_lat = latitudes[segment]
    start_lon = longitudes[segment]

    end_lat = latitudes[segment + 1]
    end_lon = longitudes[segment + 1]

    for step in range(steps_per_segment + 1):

        progress = step / steps_per_segment

        current_lat = (
            start_lat
            + progress * (end_lat - start_lat)
        )

        current_lon = (
            start_lon
            + progress * (end_lon - start_lon)
        )

        route_lats = latitudes[:segment + 1] + [current_lat]
        route_lons = longitudes[:segment + 1] + [current_lon]

        city_labels = (
            locations[:segment + 1]
            + [locations[segment + 1]]
        )

        transport = transports[segment]

        transport_icon = TRANSPORT_TYPES.get(
            transport,
            "❓"
        )


        frames.append(
            go.Frame(
                data=[
                    go.Scattergeo(
                        lon=route_lons,
                        lat=route_lats,
                        mode="lines+markers+text",
                        text=city_labels,
                        textposition="top center",
                        line=dict(
                            width=4,
                            color="royalblue"
                        ),
                        marker=dict(
                            size=8,
                            color="royalblue"
                        )
                    )
                ],
                layout=go.Layout(
                    title=(
                        f"{transport_icon} "
                        f"{locations[segment]} → "
                        f"{locations[segment + 1]}"
                    )
                ),
                name=str(frame_number)
            )
        )

        frame_number += 1

# -----------------------------
# Initial Figure
# -----------------------------

fig = go.Figure(
    data=[
        go.Scattergeo(
            lon=[longitudes[0]],
            lat=[latitudes[0]],
            mode="markers+text",
            text=[locations[0]],
            textposition="top center",
            marker=dict(
                size=10,
                color="royalblue"
            )
        )
    ],
    frames=frames
)

# -----------------------------
# Layout
# -----------------------------

fig.update_layout(
    title="Travel Documentary Generator V0.3 Gamma",
    geo=dict(
        projection_type="natural earth",
        showland=True,
        showcountries=True,
        lataxis=dict(
            range=[min_lat, max_lat]
        ),
        lonaxis=dict(
            range=[min_lon, max_lon]
        )
    ),
    updatemenus=[
        dict(
            type="buttons",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {
                                "duration": 100,
                                "redraw": True
                            },
                            "fromcurrent": True
                        }
                    ]
                )
            ]
        )
    ]
)

fig.show()