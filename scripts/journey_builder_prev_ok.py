import streamlit as st
import folium

from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# -------------------------------------------------
# Page
# -------------------------------------------------

st.set_page_config(
    page_title="Journey Builder",
    layout="wide"
)

st.title("🌏 Travel Documentary Generator")
st.subheader("Journey Builder V0.5 Alpha")

# -------------------------------------------------
# Session State
# -------------------------------------------------

if "map_lat" not in st.session_state:
    st.session_state.map_lat = 0

if "map_lon" not in st.session_state:
    st.session_state.map_lon = 0

if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = 2

if "marker" not in st.session_state:
    st.session_state.marker = None

if "location_name" not in st.session_state:
    st.session_state.location_name = ""

if "latitude" not in st.session_state:
    st.session_state.latitude = ""

if "longitude" not in st.session_state:
    st.session_state.longitude = ""

# -------------------------------------------------
# Search
# -------------------------------------------------

search_text = st.text_input(
    "Search Location",
    value=""
)

# -------------------------------------------------
# Locate Button
# -------------------------------------------------

if st.button("Locate"):

    geo = Nominatim(
        user_agent="travel_documentary_generator",
        timeout=10
    )

    location = geo.geocode(search_text)

    if location:

        st.session_state.location_name = location.address

        st.session_state.latitude = location.latitude
        st.session_state.longitude = location.longitude

        st.session_state.map_lat = location.latitude
        st.session_state.map_lon = location.longitude

        st.session_state.zoom_level = 15

        st.session_state.marker = (
            location.latitude,
            location.longitude
        )

    else:

        st.error("Location not found")

# -------------------------------------------------
# Selected Location
# -------------------------------------------------

st.markdown("---")

st.subheader("Selected Location")

st.write(
    f"**Name:** {st.session_state.location_name}"
)

st.write(
    f"**Latitude:** {st.session_state.latitude}"
)

st.write(
    f"**Longitude:** {st.session_state.longitude}"
)

# -------------------------------------------------
# Map
# -------------------------------------------------

m = folium.Map(
    location=[
        st.session_state.map_lat,
        st.session_state.map_lon
    ],
    zoom_start=st.session_state.zoom_level
)

if st.session_state.marker:

    folium.Marker(
        st.session_state.marker,
        tooltip=st.session_state.location_name
    ).add_to(m)

st_folium(
    m,
    width=1400,
    height=700
)