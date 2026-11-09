import streamlit as st
import folium
import pandas as pd

from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# -----------------------------
# Transport Types
# -----------------------------

TRANSPORT_TYPES = [
    "Walking",
    "Bicycle",
    "Motorbike",
    "Car",
    "Bus",
    "Train",
    "Plane",
    "Helicopter",
    "Drone",
    "Ship",
    "Boat",
    "Swimming",
    "Horse",
    "Camel",
    "Donkey"
]


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

if "trip_rows" not in st.session_state:
    st.session_state.trip_rows = []

if "clicked_lat" not in st.session_state:
    st.session_state.clicked_lat = None

if "clicked_lon" not in st.session_state:
    st.session_state.clicked_lon = None    

# -------------------------------------------------
# Layout 25% / 75%
# -------------------------------------------------


# left_col, right_col = st.columns([1, 3])

left_col, right_col = st.columns([2, 3])

# =================================================
# LEFT SIDE
# =================================================

with left_col:

    st.markdown("## 🌏 Journey Builder")

    # ==========================================
    # START POINT
    # ==========================================

    st.markdown("##### Start Point")

    start_search = st.text_input(
        "",
        placeholder="Choose starting point or right click on the map",
        key="start_search"
    )

    start_locate = st.button(
        "🔍 Search Start",
        key="start_locate"
    )

    if start_locate:

        geo = Nominatim(
            user_agent="travel_documentary_generator",
            timeout=10
        )

        location = geo.geocode(start_search)

        if location:

            st.session_state.start_name = start_search

            st.session_state.start_lat = location.latitude
            st.session_state.start_lon = location.longitude

            st.session_state.map_lat = location.latitude
            st.session_state.map_lon = location.longitude

            st.session_state.zoom_level = 15

            st.session_state.marker = (
                location.latitude,
                location.longitude
            )

        else:

            st.error(
                "Start Point not found"
            )

    st.write(
        f"**Coordinates:** "
        f"({st.session_state.get('start_lat','')}, "
        f"{st.session_state.get('start_lon','')})"
    )

    # st.markdown("---")

    # ==========================================
    # END POINT
    # ==========================================

    st.markdown("##### End Point")

    end_search = st.text_input(
        "",
        placeholder="Choose destination point or right click on the map",
        key="end_search"
    )

    end_locate = st.button(
        "🔍 Search End",
        key="end_locate"
    )

    if end_locate:

        geo = Nominatim(
            user_agent="travel_documentary_generator",
            timeout=10
        )

        location = geo.geocode(end_search)

        if location:

            st.session_state.end_name = end_search

            st.session_state.end_lat = location.latitude
            st.session_state.end_lon = location.longitude

        else:

            st.error(
                "End Point not found"
            )

    st.write(
        f"**Coordinates:** "
        f"({st.session_state.get('end_lat','')}, "
        f"{st.session_state.get('end_lon','')})"
    )

    # st.markdown("---")

    # ==========================================
    # TRANSPORT
    # ==========================================

    transport = st.selectbox(
        "Transport",
        TRANSPORT_TYPES,
        key="transport"
    )

    if st.button(
        "Add Trip",
        key="add_trip"
    ):

        if (
            st.session_state.get("start_name")
            and
            st.session_state.get("end_name")
        ):

            st.session_state.trip_rows.append(
                {
                    "Trip":
                        len(st.session_state.trip_rows) + 1,

                    "Start Point":
                        st.session_state.start_name,

                    "End Point":
                        st.session_state.end_name,

                    "Transport":
                        transport,

                    "Coord. From":
                        f"{st.session_state.start_lat:.4f}, "
                        f"{st.session_state.start_lon:.4f}",

                    "Coord. To":
                        f"{st.session_state.end_lat:.4f}, "
                        f"{st.session_state.end_lon:.4f}",

                    "Animate Route":
                        True
                }
            )

    # st.markdown("---")

    # ==========================================
    # MAP CLICK
    # ==========================================

    st.markdown("##### Last Map Click")

    if (
        st.session_state.clicked_lat
        and
        st.session_state.clicked_lon
    ):

        st.success(
            f"({st.session_state.clicked_lat:.6f}, "
            f"{st.session_state.clicked_lon:.6f})"
        )

    else:

        st.info(
            "Click anywhere on the map to select a location."
        )


    # ==========================================
    # JOURNEY TABLE
    # ==========================================

    st.markdown(
        "<h3 style='text-align:center'>Journey Table</h3>",
        unsafe_allow_html=True
    )

    if st.session_state.trip_rows:

        trip_df = pd.DataFrame(
            st.session_state.trip_rows
        )

        trip_df_display = trip_df[
            [
                "Trip",
                "Start Point",
                "End Point",
                "Transport",
                "Animate Route"
            ]
        ]

        st.dataframe(
            trip_df_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No trips defined yet."
        )
# =================================================
# RIGHT SIDE
# =================================================

with right_col:

    apply_click_to = st.radio(
        "Apply Map Click To",
        [
            "None",
            "Start Point",
            "End Point"
        ],
        index=0,
        horizontal=True
    )


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

    map_data = st_folium(
        m,
        width=None,
        height=1400,
        returned_objects=["last_clicked"]
    )

    # st.json(map_data)

if (
    map_data
    and map_data.get("last_clicked")
):

    st.session_state.clicked_lat = (
        map_data["last_clicked"]["lat"]
    )

    st.session_state.clicked_lon = (
        map_data["last_clicked"]["lng"]
    )


# ---------------------------------
# APPLY LAST CLICK
# ---------------------------------

if (
    use_map_click
    and st.session_state.clicked_lat
    and st.session_state.clicked_lon
):

    if apply_click_to == "Start Point":

        st.session_state.start_lat = (
            st.session_state.clicked_lat
        )

        st.session_state.start_lon = (
            st.session_state.clicked_lon
        )

        st.session_state.start_name = (
            f"Map Point "
            f"({st.session_state.clicked_lat:.4f}, "
            f"{st.session_state.clicked_lon:.4f})"
        )

        st.success(
            "Applied to Start Point"
        )

    elif apply_click_to == "End Point":

        st.session_state.end_lat = (
            st.session_state.clicked_lat
        )

        st.session_state.end_lon = (
            st.session_state.clicked_lon
        )

        st.session_state.end_name = (
            f"Map Point "
            f"({st.session_state.clicked_lat:.4f}, "
            f"{st.session_state.clicked_lon:.4f})"
        )

        st.success(
            "Applied to End Point"
        )

    elif apply_click_to == "None":

        st.warning(
            "Select Start Point or End Point first."
        )


        # st.write(
        #     f"Clicked: "
        #     f"({st.session_state.clicked_lat}, "
        #     f"{st.session_state.clicked_lon})"
        # )        

