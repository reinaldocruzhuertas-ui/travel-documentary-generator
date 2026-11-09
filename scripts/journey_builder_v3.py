import streamlit as st
import folium
import pandas as pd

from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# -----------------------------
# Transport Types
# -----------------------------
TRANSPORT_TYPES = [
    "Walking", "Bicycle", "Motorbike", "Car", "Bus", "Train", "Plane", 
    "Helicopter", "Drone", "Ship", "Boat", "Swimming", "Horse", "Camel", "Donkey"
]

# -------------------------------------------------
# Page
# -------------------------------------------------
st.set_page_config(page_title="Journey Builder", layout="wide")

# -------------------------------------------------
# Session State
# -------------------------------------------------
if "map_lat" not in st.session_state: st.session_state.map_lat = -33.8568
if "map_lon" not in st.session_state: st.session_state.map_lon = 151.2153
if "zoom_level" not in st.session_state: st.session_state.zoom_level = 12

if "marker" not in st.session_state: st.session_state.marker = None
if "location_name" not in st.session_state: st.session_state.location_name = ""

if "start_search" not in st.session_state: st.session_state.start_search = ""
if "end_search" not in st.session_state: st.session_state.end_search = ""

if "_last_processed_click" not in st.session_state: st.session_state._last_processed_click = None
if "trip_rows" not in st.session_state: st.session_state.trip_rows = []

if "pending_start_name" not in st.session_state: st.session_state.pending_start_name = None
if "pending_end_name" not in st.session_state: st.session_state.pending_end_name = None

# Apply pending updates BEFORE widgets are created
if st.session_state.pending_start_name is not None:
    st.session_state.start_search = st.session_state.pending_start_name
    st.session_state.pending_start_name = None

if st.session_state.pending_end_name is not None:
    st.session_state.end_search = st.session_state.pending_end_name
    st.session_state.pending_end_name = None

# -------------------------------------------------
# Layout
# -------------------------------------------------
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

    st.text_input(
        "Start location name",
        key="start_search",
        placeholder="Search a place, or click the map to drop the start point",
    )

    start_locate = st.button("🔍 Search Start", key="start_locate")

    if start_locate:
        geo = Nominatim(user_agent="travel_documentary_generator", timeout=10)
        location = geo.geocode(st.session_state.start_search)
        if location:
            st.session_state.start_name = st.session_state.start_search
            st.session_state.start_lat = location.latitude
            st.session_state.start_lon = location.longitude
            st.session_state.map_lat = location.latitude
            st.session_state.map_lon = location.longitude
            st.session_state.zoom_level = 15
            st.session_state.marker = (location.latitude, location.longitude)
            st.session_state.location_name = st.session_state.start_search
        else:
            st.error("Start Point not found")

    st.write(f"**Coordinates:** ({st.session_state.get('start_lat','')}, {st.session_state.get('start_lon','')})")

    # ==========================================
    # END POINT
    # ==========================================
    st.markdown("##### End Point")

    st.text_input(
        "End location name",
        key="end_search",
        placeholder="Search a place, or click the map to drop the end point",
    )

    end_locate = st.button("🔍 Search End", key="end_locate")

    if end_locate:
        geo = Nominatim(user_agent="travel_documentary_generator", timeout=10)
        location = geo.geocode(st.session_state.end_search)
        if location:
            st.session_state.end_name = st.session_state.end_search
            st.session_state.end_lat = location.latitude
            st.session_state.end_lon = location.longitude
        else:
            st.error("End Point not found")

    st.write(f"**Coordinates:** ({st.session_state.get('end_lat','')}, {st.session_state.get('end_lon','')})")

    # ==========================================
    # TRANSPORT & JOURNEY TABLE
    # ==========================================
    transport = st.selectbox("Transport", TRANSPORT_TYPES, key="transport")

    if st.button("Add Trip", key="add_trip"):
        if st.session_state.get("start_name") and st.session_state.get("end_name"):
            st.session_state.trip_rows.append({
                "Trip": len(st.session_state.trip_rows) + 1,
                "Start Point": st.session_state.start_name,
                "End Point": st.session_state.end_name,
                "Transport": transport,
                "Coord. From": f"{st.session_state.start_lat:.4f}, {st.session_state.start_lon:.4f}",
                "Coord. To": f"{st.session_state.end_lat:.4f}, {st.session_state.end_lon:.4f}",
                "Animate Route": True
            })

    st.markdown("<h3 style='text-align:center'>Journey Table</h3>", unsafe_allow_html=True)

    if st.session_state.trip_rows:
        trip_df = pd.DataFrame(st.session_state.trip_rows)
        trip_df_display = trip_df[["Trip", "Start Point", "End Point", "Transport", "Animate Route"]]
        st.dataframe(trip_df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No trips defined yet.")

# =================================================
# RIGHT SIDE
# =================================================
with right_col:
    # THE FIX: Bold text and added "None" option
    click_target = st.radio(
        "**Where should the next map click be assigned?**",
        options=["Start Point", "End Point", "None"],
        horizontal=True,
        key="map_target_radio"
    )

    # Create the map with current state values
    m = folium.Map(location=[st.session_state.map_lat, st.session_state.map_lon], zoom_start=st.session_state.zoom_level)

    if st.session_state.marker:
        folium.Marker(st.session_state.marker, tooltip=st.session_state.location_name).add_to(m)

    map_data = st_folium(
        m, 
        width=None, 
        height=750, 
        key="journey_map", 
        returned_objects=["last_clicked"]
    )

    # ---------------------------------------------
    # Click handling
    # ---------------------------------------------
    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        
        lat = round(clicked["lat"], 5)
        lon = round(clicked["lng"], 5)
        click_key = (lat, lon)

        # Do nothing if "None" is selected or if it's the exact same click as before
        if click_target != "None" and click_key != st.session_state._last_processed_click:
            st.session_state._last_processed_click = click_key

            # Reverse geocode
            geo = Nominatim(user_agent="travel_documentary_generator", timeout=10)
            try:
                location = geo.reverse(f"{lat}, {lon}")
                
                name_part = location.raw.get("name", "") if location else ""
                if not name_part and location:
                    name_part = location.address.split(",")[0]
                    
                if name_part.isdigit() or not name_part:
                    auto_name = f"Point {lat:.4f}, {lon:.4f}"
                else:
                    auto_name = name_part
                    
            except Exception:
                auto_name = f"Point {lat:.4f}, {lon:.4f}"

            # Assign to the correct target based on the Radio Button
            if click_target == "Start Point":
                st.session_state.start_lat = lat
                st.session_state.start_lon = lon
                st.session_state.start_name = auto_name
                st.session_state.pending_start_name = auto_name
            else: # It must be "End Point" at this point
                st.session_state.end_lat = lat
                st.session_state.end_lon = lon
                st.session_state.end_name = auto_name
                st.session_state.pending_end_name = auto_name

            # Update map marker and center on the clicked point
            st.session_state.marker = (lat, lon)
            st.session_state.location_name = auto_name
            st.session_state.map_lat = lat
            st.session_state.map_lon = lon
            
            st.rerun()

    with st.expander("Debug: last map_data"):
        st.write(map_data)