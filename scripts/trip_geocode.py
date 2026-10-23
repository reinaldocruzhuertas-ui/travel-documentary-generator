import pandas as pd
from geopy.geocoders import Nominatim
import time

# Read trip file
trip = pd.read_csv("data/trip.csv")

# Extract unique locations
locations = set()

for _, row in trip.iterrows():
    locations.add(row["From"])
    locations.add(row["To"])

print("Locations found:")
print()

# Create geocoder
geo = Nominatim(
    user_agent="travel_documentary_generator",
    timeout=10
)

# Lookup coordinates
for city in sorted(locations):

    location = geo.geocode(f"{city} Australia")

    if location:
        print(
            f"{city}: "
            f"{location.latitude}, "
            f"{location.longitude}"
        )

    time.sleep(1)