import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time

print("Reading trip file...")

trip = pd.read_csv("data/trip.csv")

print("Trip loaded")
print()

# Extract locations in travel order
locations = []

locations.append(trip.iloc[0]["From"])

for _, row in trip.iterrows():
    locations.append(row["To"])

print("Locations found:")

for location in locations:
    print(location)

print()

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

print()
print("Drawing map...")

fig = go.Figure()

fig.add_trace(
    go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode="lines+markers+text",
        text=locations,
        textposition="top center",
        line=dict(width=3),
        marker=dict(size=10)
    )
)

fig.update_layout(
    title="Travel Documentary Generator V0.2",
    geo=dict(
        projection_type="natural earth",
        showland=True
    )
)

fig.show()