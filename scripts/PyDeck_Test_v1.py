import streamlit as st
import pydeck as pdk

st.title("PyDeck Map with Hill Relief")

# Using an open topography tile provider (OpenTopoMap) which includes hill shading and contour lines
terrain_layer = pdk.Layer(
    "TileLayer",
    data="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    min_zoom=0,
    max_zoom=17,
    tileSize=256,
    subdomains=["a", "b", "c"],
)

view_state = pdk.ViewState(
    latitude=46.24,
    longitude=-122.18,
    zoom=11,
    pitch=30,  # Slight tilt to highlight the terrain
)

r = pdk.Deck(
    layers=[terrain_layer],
    initial_view_state=view_state,
    map_style=None,
)

st.pydeck_chart(r)