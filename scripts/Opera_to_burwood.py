import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath

# Page configuration
st.set_page_config(page_title="Train Journey Animation", layout="wide")

st.title("🚆 Train Route Animation: Sydney Opera House to Burwood Station")
st.markdown("This map uses OpenStreetMap tiles with a smooth, non-blinking animated route flow.")

# Initialize map
m = folium.Map(location=[-33.865, 151.15], zoom_start=12, tiles="OpenStreetMap")

# 1. Define train route coordinates passing along the line
train_route = [
    [-33.857198, 151.2151234],  # Opera House
    [-33.861400, 151.210800],  # Circular Quay
    [-33.873500, 151.206500],  # CBD / Town Hall area
    [-33.883000, 151.200000],  # Redfern area
    [-33.878000, 151.150000],  # Inner West
    [-33.8771445, 151.1040382] # Burwood Station
]

# 2. Add static Start & End Markers
folium.Marker(
    train_route[0], 
    tooltip="Start: Sydney Opera House", 
    icon=folium.Icon(color="red", icon="play", prefix="fa")
).add_to(m)

folium.Marker(
    train_route[-1], 
    tooltip="End: Sydney Burwood Station", 
    icon=folium.Icon(color="blue", icon="stop", prefix="fa")
).add_to(m)

# 3. Add the smooth, non-blinking AntPath animation overlay
AntPath(
    locations=train_route,
    color="#1f77b4",          # Train route line color
    weight=6,                 # Thickness of the line
    opacity=0.8,
    pulse_color="#ffffff",    # Glowing moving pulse effect
    delay=800,                # Speed of the animation flow
    dash_array=[10, 20]
).add_to(m)

# 4. Render the completely stable map in Streamlit
st_folium(m, width=1000, height=550)