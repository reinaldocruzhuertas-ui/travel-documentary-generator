import streamlit as st
import pydeck as pdk

st.title("High-Definition PyDeck Map")

# Define data (e.g., a path or coordinates)
data = [
    {"name": "Point A", "coordinates": [-74.0060, 40.7128]},
    {"name": "Point B", "coordinates": [-73.9352, 40.7306]}
]

# Set initial view pointing at New York
view_state = pdk.ViewState(
    latitude=40.7128,
    longitude=-74.0060,
    zoom=12,
    pitch=0,
)

# Create a crisp Scatterplot layer
layer = pdk.Layer(
    "ScatterplotLayer",
    data=data,
    get_position="coordinates",
    get_radius=150,
    get_fill_color=[0, 128, 255, 200],  # Crisp blue with transparency
    pickable=True,
)

# Render the deck with a clean, modern map style
r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="light",  # Built-in crisp vector style (no token required)
    tooltip={"text": "{name}"}
)

st.pydeck_chart(r)