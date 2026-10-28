import streamlit as st
import folium
import pandas as pd

from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# -------------------------------------------------
# Page
# -------------------------------------------------

st.set_page_config(
    page_title="Journey Builder",
    layout="wide"
)

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

if "journey_points" not in st.session_state:
    st.session_state.journey_points = []

# -------------------------------------------------
# Layout 25% / 75%
# -------------------------------------------------

left_col, right_col = st.columns([1, 3])

# =================================================
# LEFT SIDE
# =================================================

with left_col:

    st.title("🌏 Journey Builder")

    st.subheader("Search Location")

    search_text = st.text_input(
        "",
        placeholder="Sydney Opera House"
    )

    if st.button("Locate"):

        geo = Nominatim(
            user_agent="travel_documentary_generator",
            timeout=10
        )

        location = geo.geocode(search_text)

        if location:

            st.session_state.location_name = search_text

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

            st.error(
                "Location not found"
            )

    st.markdown("---")

    st.subheader("Journey Point")

    point_name = st.text_input(
        "Point Name",
        value=st.session_state.location_name
    )

    st.write(
        f"Coordinates: "
        f"({st.session_state.latitude}, "
        f"{st.session_state.longitude})"
    )

    if st.button("Add Journey Point"):

        if (
            point_name
            and st.session_state.latitude != ""
        ):

            st.session_state.journey_points.append(
                {
                    "Point Name": point_name,
                    "Coordinates":
                        f"({st.session_state.latitude}, "
                        f"{st.session_state.longitude})"
                }
            )

            st.success(
                f"Added: {point_name}"
            )

    st.markdown("---")

    st.subheader("Journey Points")

    if st.session_state.journey_points:

        points_df = pd.DataFrame(
            st.session_state.journey_points
        )

        st.dataframe(
            points_df,
            use_container_width=True
        )

    else:

        st.info(
            "No Journey Points added yet."
        )

# =================================================
# RIGHT SIDE
# =================================================

with right_col:

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
        height=800
    )