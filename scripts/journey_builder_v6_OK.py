import streamlit as st
import folium
import pandas as pd

from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# -----------------------------
# Transport Types & Emojis
# -----------------------------
TRANSPORT_TYPES = [
    "Walking", "Bicycle", "Motorbike", "Car", "Bus", "Train", "Plane", 
    "Helicopter", "Drone", "Ship", "Boat", "Swimming", "Horse", "Camel", "Donkey"
]

TRANSPORT_EMOJIS = {
    "Walking": "🚶", "Bicycle": "🚲", "Motorbike": "🏍️", "Car": "🚗", 
    "Bus": "🚌", "Train": "🚆", "Plane": "✈️", "Helicopter": "🚁", 
    "Drone": "🛸", "Ship": "🚢", "Boat": "⛵", "Swimming": "🏊", 
    "Horse": "🐎", "Camel": "🐫", "Donkey": "🫏"
}

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
if "saved_last_click" not in st.session_state: st.session_state.saved_last_click = None

# Apply pending updates BEFORE widgets are created
if st.session_state.pending_start_name is not None:
    st.session_state.start_search = st.session_state.pending_start_name
    st.session_state.pending_start_name = None

if st.session_state.pending_end_name is not None:
    st.session_state.end_search = st.session_state.pending_end_name
    st.session_state.pending_end_name = None

# -------------------------------------------------
# Callbacks
# -------------------------------------------------
def sync_table_edits():
    """This runs BEFORE the rerun when a checkbox or delete is clicked."""
    editor_state = st.session_state.journey_table_editor
    
    # Start with the original data
    updated_rows = st.session_state.trip_rows.copy()
    
    # 1. Handle Deletions (If the user clicked the trash can)
    if "deleted_rows" in editor_state:
        # deleted_rows gives us a list of indices. We sort them in reverse 
        # so deleting a row doesn't mess up the index of the next row to delete.
        for idx in sorted(editor_state["deleted_rows"], reverse=True):
            updated_rows.pop(idx)
            
        # Re-number the "Trip" column so it stays 1, 2, 3...
        for i, row in enumerate(updated_rows):
            row["Trip"] = i + 1

    # 2. Handle Edits (If the user ticked a checkbox)
    if "edited_rows" in editor_state:
        for row_idx, changes in editor_state["edited_rows"].items():
            # Make sure the row still exists (it might have been deleted)
            if row_idx < len(updated_rows):
                for col_name, new_value in changes.items():
                    updated_rows[row_idx][col_name] = new_value
                    
    # Save it back to session state
    st.session_state.trip_rows = updated_rows

        
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
                "Start Lat": st.session_state.start_lat,
                "Start Lon": st.session_state.start_lon,
                "End Lat": st.session_state.end_lat,
                "End Lon": st.session_state.end_lon,
                "Animate Route": False 
            })

    st.markdown("<h3 style='text-align:center'>Journey Table</h3>", unsafe_allow_html=True)

    # (Inside the left_col block, replacing your current data_editor)
    if st.session_state.trip_rows:
        trip_df = pd.DataFrame(st.session_state.trip_rows)

        # Add a small caption to explain the delete column
        st.caption("🗑️ Hover over the left edge of a row to delete a trip.")        
        
        st.data_editor(
            trip_df,
            column_config={
                "Animate Route": st.column_config.CheckboxColumn(
                    "Animate Route",
                    help="Check to animate on the map",
                    default=False,
                )
            },
            column_order=["Trip", "Start Point", "End Point", "Transport", "Animate Route"],
            use_container_width=True,
            hide_index=True,
            disabled=["Trip", "Start Point", "End Point", "Transport"],
            key="journey_table_editor",
            on_change=sync_table_edits,
            num_rows="dynamic"  # <--- THIS IS THE NEW LINE
        )
    else:
        st.info("No trips defined yet.")


# =================================================
# RIGHT SIDE
# =================================================
with right_col:
    click_target = st.radio(
        "**Where should the next map click be assigned?**",
        options=["Start Point", "End Point", "None"],
        horizontal=True,
        key="map_target_radio"
    )

    m = folium.Map(location=[st.session_state.map_lat, st.session_state.map_lon], zoom_start=st.session_state.zoom_level)

    if st.session_state.marker:
        folium.Marker(st.session_state.marker, tooltip=st.session_state.location_name).add_to(m)

    # -------------------------------------------------
    # DRAW ANIMATED ROUTES AND EMOJIS
    # -------------------------------------------------
    # Variables to calculate map bounds for zooming
    route_bounds = []
    
    for trip in st.session_state.trip_rows:
        if trip.get("Animate Route", False):
            
            start_coord = [trip["Start Lat"], trip["Start Lon"]]
            end_coord = [trip["End Lat"], trip["End Lon"]]
            transport_type = trip["Transport"]
            emoji = TRANSPORT_EMOJIS.get(transport_type, "📍")
            
            route_bounds.extend([start_coord, end_coord])
            
            # 1. Emoji at Start Point
            folium.Marker(
                location=start_coord,
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 24px; text-align: center;">{emoji}</div>',
                    icon_size=(30, 30),
                    icon_anchor=(15, 15)
                ),
                tooltip=f"{emoji} {transport_type} to {trip['End Point']}"
            ).add_to(m)
            
            # THE FIX for #1: Add a standard blue pin at the End Point
            folium.Marker(
                location=end_coord,
                tooltip=f"Arrival: {trip['End Point']}"
            ).add_to(m)
            
            # 2. Animated Line
            folium.plugins.AntPath(
                locations=[start_coord, end_coord],
                dash_array=[10, 20],
                delay=800,
                color='#FF5733',
                pulse_color='#FFF',
                weight=5,
                tooltip=f"{transport_type}: {trip['Start Point']} ➔ {trip['End Point']}"
            ).add_to(m)
            
            # 3. Base Line
            folium.PolyLine(
                locations=[start_coord, end_coord],
                color='gray',
                weight=2,
                opacity=0.5
            ).add_to(m)

    # THE FIX for #2: Auto-zoom if there are newly animated routes
    if route_bounds:
        # Calculate the rough center and center the map there
        lats = [b[0] for b in route_bounds]
        lons = [b[1] for b in route_bounds]
        center_lat = (max(lats) + min(lats)) / 2
        center_lon = (max(lons) + min(lons)) / 2
        
        # If the map is far away from the route, snap to it
        # (We use a small threshold so it doesn't jerk around if you're already looking at it)
        if abs(st.session_state.map_lat - center_lat) > 0.05 or abs(st.session_state.map_lon - center_lon) > 0.05:
            st.session_state.map_lat = center_lat
            st.session_state.map_lon = center_lon
            st.session_state.zoom_level = 12 # Zoom out a bit to fit the route
            st.rerun() # Rerun to apply the new center immediately

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

        if click_target != "None" and click_key != st.session_state._last_processed_click:
            st.session_state._last_processed_click = click_key
            st.session_state.saved_last_click = {"lat": lat, "lng": lon}

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

            if click_target == "Start Point":
                st.session_state.start_lat = lat
                st.session_state.start_lon = lon
                st.session_state.start_name = auto_name
                st.session_state.pending_start_name = auto_name
            else:
                st.session_state.end_lat = lat
                st.session_state.end_lon = lon
                st.session_state.end_name = auto_name
                st.session_state.pending_end_name = auto_name

            st.session_state.marker = (lat, lon)
            st.session_state.location_name = auto_name
            st.session_state.map_lat = lat
            st.session_state.map_lon = lon
            
            st.rerun()

    with st.expander("Debug: Last Clicked Coordinates"):
        st.write(st.session_state.saved_last_click)