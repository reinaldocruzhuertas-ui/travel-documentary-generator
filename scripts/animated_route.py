import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time
import os

# ---------------------------------
# Read trip file
# ---------------------------------

trip = pd.read_csv("data/trip.csv")

locations = []

locations.append(trip.iloc[0]["From"])

for _, row in trip.iterrows():
    locations.append(row["To"])

# ---------------------------------
# Geocode locations
# ---------------------------------

geo = Nominatim(
    user_agent="travel_documentary_generator",
    timeout=10
)

latitudes = []
longitudes = []

print("Getting coordinates...")

for city in locations:

    location = geo.geocode(f"{city} Australia")

    if location:

        latitudes.append(location.latitude)
        longitudes.append(location.longitude)

        print(
            f"{city}: "
            f"{location.latitude}, "
            f"{location.longitude}"
        )

    time.sleep(1)

# ---------------------------------
# Create output folder
# ---------------------------------

os.makedirs("output/frames", exist_ok=True)

# ---------------------------------
# Generate frames
# ---------------------------------

frame_number = 1

steps_per_segment = 20

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

        route_lats = latitudes[:segment + 1]
        route_lons = longitudes[:segment + 1]

        route_lats = route_lats + [current_lat]
        route_lons = route_lons + [current_lon]

        fig = go.Figure()

        fig.add_trace(
            go.Scattergeo(
                lon=route_lons,
                lat=route_lats,
                mode="lines+markers",
                line=dict(width=4),
                marker=dict(size=8)
            )
        )

        fig.update_layout(
            title=f"Frame {frame_number}",
            geo=dict(
                projection_type="natural earth",
                showland=True
            )
        )

        filename = (
            f"output/frames/frame_{frame_number:03d}.html"
        )

        fig.write_html(filename)

        print(f"Created {filename}")

        frame_number += 1

print()
print("Route animation frames generated.")