import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath, Draw

# Page configuration
st.set_page_config(page_title="Draw Your Train Route", layout="wide")

st.title("🚆 Draw Your Own Train Route Animation")
st.markdown("Use the **line tool** on the left side of the map to click-and-draw your precise train track from the Opera House to Burwood Station!")

# Initialize map centered on Sydney
m = folium.Map(location=[-33.865, 151.15], zoom_start=12, tiles="OpenStreetMap")

# Add the Drawing Toolbar to the map
draw = Draw(
    export=False,
    position="topleft",
    draw_options={
        'polyline': True,    # Allow drawing lines (rails/routes)
        'polygon': False,
        'rectangle': False,
        'circle': False,
        'marker': False,
        'circlemarker': False,
    },
    edit_options={'edit': True}
)
draw.add_to(m)

# Capture user interactions and drawings from Streamlit-Folium
output = st_folium(m, width=1000, height=550)

# Check if the user has drawn a path on the map
drawn_route = None
if output and output.get("last_active_drawing"):
    drawing = output["last_active_drawing"]
    if drawing["geometry"]["type"] == "LineString":
        # GeoJSON stores coordinates as [Longitude, Latitude]. 
        # Folium/Leaflet needs them swapped to [Latitude, Longitude].
        raw_coords = drawing["geometry"]["coordinates"]
        drawn_route = [[coord[1], coord[0]] for coord in raw_coords]

# If a route has been drawn, render the animated AntPath over it!
if drawn_route:
    st.success(f"✅ Custom route captured successfully with {len(drawn_route)} points!")
    
    # Create a secondary map to display the final animated result
    anim_map = folium.Map(location=[-33.865, 151.15], zoom_start=12, tiles="OpenStreetMap")
    
    # Add start/end station markers
    start_train_icon = folium.DivIcon(
        html='<div style="font-size: 20px; background: white; border: 3px solid #d9534f; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.3);">🚆</div>',
        icon_size=(40, 40), icon_anchor=(20, 20)
    )
    end_train_icon = folium.DivIcon(
        html='<div style="font-size: 20px; background: white; border: 3px solid #0275d8; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 6px rgba(0,0,0,0.3);">🚆</div>',
        icon_size=(40, 40), icon_anchor=(20, 20)
    )
    
    folium.Marker(drawn_route[0], tooltip="Start: Sydney Opera House", icon=start_train_icon).add_to(anim_map)
    folium.Marker(drawn_route[-1], tooltip="End: Burwood Station", icon=end_train_icon).add_to(anim_map)
    
    # Animate along the exact user-drawn coordinates
    AntPath(
        locations=drawn_route,
        color="#0055ff",
        weight=6,
        opacity=0.85,
        pulse_color="#ffcc00",
        delay=700,
        dash_array=[12, 20]
    ).add_to(anim_map)
    
    st.markdown("### 🎬 Rendered Animation on Your Custom Path:")
    st_folium(anim_map, width=1000, height=450)
else:
    st.info("💡 **Tip:** Click the polyline/line icon in the top-left toolbar of the map above, click your way along the railway tracks from the Opera House to Burwood, and double-click to finish your line!")