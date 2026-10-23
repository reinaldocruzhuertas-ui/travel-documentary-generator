from geopy.geocoders import Nominatim

# Create geocoder
geo = Nominatim(user_agent="travel_documentary_generator")

# Search for Sydney
location = geo.geocode("Sydney Australia")

print("Location:", location.address)
print("Latitude:", location.latitude)
print("Longitude:", location.longitude)


# Search for Sydney
location = geo.geocode("Melbourne Australia")

print("Location:", location.address)
print("Latitude:", location.latitude)
print("Longitude:", location.longitude)