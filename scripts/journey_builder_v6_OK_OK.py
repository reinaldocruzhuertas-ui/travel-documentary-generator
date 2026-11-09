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
if "debug_paths" not in st.session_state: st.session_state.debug_paths = []

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
    editor_state = st.session_state.journey_table_editor
    updated_rows = st.session_state.trip_rows.copy()
    
    if "deleted_rows" in editor_state:
        for idx in sorted(editor_state["deleted_rows"], reverse=True):
            updated_rows.pop(idx)
        for i, row in enumerate(updated_rows):
            row["Trip"] = i + 1

    if "edited_rows" in editor_state:
        for row_idx, changes in editor_state["edited_rows"].items():
            if row_idx < len(updated_rows):
                for col_name, new_value in changes.items():
                    updated_rows[row_idx][col_name] = new_value
                    
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
            
            start_lon = st.session_state.start_lon
            end_lon = st.session_state.end_lon
            
            # THE FIX: The moment the trip is added, if it's a plane and crosses the Pacific, 
            # convert the negative longitude to positive (e.g., -118 becomes 241).
            if transport == "Plane":
                lon_diff = end_lon - start_lon
                if lon_diff < -180: 
                    end_lon += 360
                elif lon_diff > 180:
                    start_lon += 360
            
            st.session_state.trip_rows.append({
                "Trip": len(st.session_state.trip_rows) + 1,
                "Start Point": st.session_state.start_name,
                "End Point": st.session_state.end_name,
                "Transport": transport,
                "Start Lat": st.session_state.start_lat,
                "Start Lon": start_lon,
                "End Lat": st.session_state.end_lat,
                "End Lon": end_lon,
                "Animate Route": False 
            })

    st.markdown("<h3 style='text-align:center'>Journey Table</h3>", unsafe_allow_html=True)

    if st.session_state.trip_rows:
        trip_df = pd.DataFrame(st.session_state.trip_rows)

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
            num_rows="dynamic"
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
    route_bounds = []
    st.session_state.debug_paths = []
    
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
            
            # 2. Standard blue pin at the End Point
            folium.Marker(
                location=end_coord,
                tooltip=f"Arrival: {trip['End Point']}"
            ).add_to(m)
            
            # Add to debug
            st.session_state.debug_paths.append({
                "Trip": trip["Trip"],
                "Type": "Straight Line",
                "Start Lat": start_coord[0],
                "Start Lon": start_coord[1],
                "End Lat": end_coord[0],
                "End Lon": end_coord[1]
            })
            
            # 3. Draw the line
            folium.plugins.AntPath(
                locations=[start_coord, end_coord],
                dash_array=[10, 20],
                delay=800,
                color='#FF5733',
                pulse_color='#FFF',
                weight=5,
                tooltip=f"{transport_type}: {trip['Start Point']} ➔ {trip['End Point']}"
            ).add_to(m)
            
            folium.PolyLine(
                locations=[start_coord, end_coord],
                color='gray',
                weight=2,
                opacity=0.5
            ).add_to(m)

    # Auto-zoom if there are newly animated routes
    if route_bounds:
        lats = [b[0] for b in route_bounds]
        lons = [b[1] for b in route_bounds]
        
        # Handle the center calculation across the International Date Line for zooming
        if max(lons) - min(lons) > 180:
            lons_adj = [l if l > 0 else l + 360 for l in lons]
            center_lon = ((max(lons_adj) + min(lons_adj)) / 2)
            if center_lon > 180: center_lon -= 360
        else:
            center_lon = (max(lons) + min(lons)) / 2
            
        center_lat = (max(lats) + min(lats)) / 2
        
        lat_diff = max(lats) - min(lats)
        lon_diff = max(lons) - min(lons)
        
        if lat_diff > 40 or lon_diff > 40:
            new_zoom = 2
        elif lat_diff > 10 or lon_diff > 10:
            new_zoom = 5
        else:
            new_zoom = 10

        if abs(st.session_state.map_lat - center_lat) > 0.05 or abs(st.session_state.map_lon - center_lon) > 0.05:
            st.session_state.map_lat = center_lat
            st.session_state.map_lon = center_lon
            st.session_state.zoom_level = new_zoom
            st.rerun()

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

    # ---------------------------------------------
    # DEBUGGER
    # ---------------------------------------------
    with st.expander("Debug: Route Calculation"):
        st.write("**Last Clicked:**", st.session_state.saved_last_click)
        
        if st.session_state.debug_paths:
            st.write("--- Paths Drawn on Map ---")
            st.dataframe(pd.DataFrame(st.session_state.debug_paths), use_container_width=True)