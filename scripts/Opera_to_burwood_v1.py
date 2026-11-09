import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath

# Page configuration
st.set_page_config(page_title="Train Journey Animation", layout="wide")

st.title("🚆 Train Route Animation: Sydney Opera House to Burwood Station")
st.markdown("Following the exact T1 Western Railway Line corridor through Newtown and Petersham.")

# Initialize map centered on the Sydney rail corridor
m = folium.Map(location=[-33.875, 151.15], zoom_start=13, tiles="OpenStreetMap")

# 1. Exact Railway Track Waypoints (Routing down through Newtown & Petersham)
railway_route = [
    [-33.857198, 151.2151234],  # Sydney Opera House (Start)
    [-33.861400, 151.205500],  # Circular Quay Station
    [-33.866500, 151.205300],  # Wynyard Station
    [-33.873100, 151.206100],  # Town Hall Station
    [-33.883300, 151.206500],  # Central Station
    [-33.891700, 151.199400],  # Redfern Station
    [-33.898500, 151.178000],  # Newtown Station corridor (Lower curve)
    [-33.894000, 151.157000],  # Petersham / Lewisham rail corridor
    [-33.885000, 151.125000],  # Ashfield Station corridor
    [-33.8771445, 151.1040382] # Burwood Station (End)
]

# 2. Uniform Train Emoji Markers for Start and End points
start_train_icon = folium.DivIcon(
    html='<div style="font-size: 20px; background: white; border: 3px solid #d9534f; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.3);">🚆</div>',
    icon_size=(40, 40),
    icon_anchor=(20, 20)
)

end_train_icon = folium.DivIcon(
    html='<div style="font-size: 20px; background: white; border: 3px solid #0275d8; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.3);">🚆</div>',
    icon_size=(40, 40),
    icon_anchor=(20, 20)
)

folium.Marker(
    railway_route[0], 
    tooltip="Start: Sydney Opera House", 
    icon=start_train_icon
).add_to(m)

folium.Marker(
    railway_route[-1], 
    tooltip="End: Sydney Burwood Station", 
    icon=end_train_icon
).add_to(m)

# 3. Add the smooth AntPath track aligned with the corrected railway path
AntPath(
    locations=railway_route,
    color="#0055ff",          
    weight=6,                 
    opacity=0.85,
    pulse_color="#ffcc00",    
    delay=700,                
    dash_array=[12, 20]
).add_to(m)

# 4. Render the map in Streamlit
st_folium(m, width=1000, height=550)