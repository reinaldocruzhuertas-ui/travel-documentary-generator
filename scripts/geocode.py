from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

geo = Nominatim(
    user_agent="travel_documentary_generator",
    timeout=10
)

cities = [
    "Sydney Australia",
    "Melbourne Australia"
]

for city in cities:

    try:

        location = geo.geocode(city)

        if location:
            print("\n---------------------")
            print("City:", city)
            print("Location:", location.address)
            print("Latitude:", location.latitude)
            print("Longitude:", location.longitude)

        else:
            print(f"Could not find {city}")

        time.sleep(1)

    except GeocoderTimedOut:
        print(f"Timeout while searching for {city}")