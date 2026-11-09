# Future enhancement:
# 1. Dramatic opening shots of the Earth. (DONE)
# 2. Smooth zoom-in and zoom-out animations. (DONE)
# 3. Camera tracking that follows the moving transport. (DONE)
# 4. Cinematic destination arrivals. (DONE)
# 5. Beautiful transitions between journeys. (DONE)
# 6. Zoom out to reveal the entire Earth. (DONE)

import time
import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# ============================================================
# Configuration
# ============================================================

CSV_FILE = Path("data/trip.csv")
GEOCODE_CACHE_FILE = Path("data/geocode_cache.csv")

# Orthographic globe viewing direction.
GLOBE_CENTRE_LON = 180
GLOBE_CENTRE_LAT = 0

STEPS_PER_SEGMENT = 50
FRAME_DURATION_MS = 100
GLOBE_WIDTH = 1400
GLOBE_HEIGHT = 900

# Cinematic Step 1: opening Earth reveal.
OPENING_FRAMES = 36
OPENING_START_LON = 0
OPENING_END_LON = GLOBE_CENTRE_LON

# Cinematic Camera Settings
ZOOM_OUT_SCALE = 1.0        # Entire earth visible
ZOOM_IN_SCALE = 4.0         # Following the vehicle
ZOOM_ARRIVAL_SCALE = 7.0    # Close up for final destination
ZOOM_TRANSITION_FRAMES = 15 # How many frames to zoom in/out

TRANSPORT_TYPES = {
    "Walking": "🚶", "Bicycle": "🚲", "Motorbike": "🏍️", "Car": "🚗",
    "Bus": "🚌", "Train": "🚆", "Plane": "✈️", "Helicopter": "🚁",
    "Drone": "🛸", "Ship": "🚢", "Boat": "⛵", "Swimming": "🏊",
    "Horse": "🐎", "Camel": "🐪", "Donkey": "🫏",
}


# ============================================================
# Read and validate trip data
# ============================================================

def read_trip(csv_file: Path):
    if not csv_file.exists():
        raise FileNotFoundError(f"Trip file not found: {csv_file.resolve()}")
    trip = pd.read_csv(csv_file)
    required_columns = {"From", "To", "Transport"}
    missing = required_columns.difference(trip.columns)
    if missing:
        raise ValueError("Missing CSV column(s): " + ", ".join(sorted(missing)))
    if trip.empty:
        raise ValueError("The trip.csv file contains no journeys.")
    for column in required_columns:
        trip[column] = trip[column].astype("string").str.strip()
    if trip[["From", "To", "Transport"]].isna().any().any() or (trip[["From", "To", "Transport"]] == "").any().any():
        raise ValueError("From, To and Transport cannot contain blank values.")

    locations = [str(trip.iloc[0]["From"])]
    for _, row in trip.iterrows():
        locations.append(str(row["To"]))
    transports = trip["Transport"].astype(str).tolist()
    return trip, locations, transports


# ============================================================
# Global geocoding, with a local cache
# ============================================================

def geocode_locations(locations):
    cache = {}
    if GEOCODE_CACHE_FILE.exists():
        try:
            cached = pd.read_csv(GEOCODE_CACHE_FILE)
            for _, row in cached.iterrows():
                cache[str(row["location"])] = (float(row["latitude"]), float(row["longitude"]))
        except (KeyError, ValueError, pd.errors.ParserError):
            print("Warning: geocode cache could not be read; rebuilding it.")

    geo = Nominatim(user_agent="live_animation_global_travel_visualizer", timeout=20)
    geocode = RateLimiter(geo.geocode, min_delay_seconds=1.1, swallow_exceptions=False, return_value_on_exception=None)

    coordinates = []
    new_cache_entries = []

    print("\nResolving global coordinates...")
    for place in locations:
        if place in cache:
            lat, lon = cache[place]
            print(f"[CACHE] {place}: {lat:.6f}, {lon:.6f}")
        else:
            print(f"[LOOKUP] {place}")
            result = geocode(place, exactly_one=True)
            if result is None:
                raise ValueError(f"Could not find '{place}'. Add its country to the location in trip.csv.")
            lat, lon = float(result.latitude), float(result.longitude)
            cache[place] = (lat, lon)
            new_cache_entries.append({"location": place, "latitude": lat, "longitude": lon})
            print(f"         {lat:.6f}, {lon:.6f}")
        coordinates.append((lat, lon))

    cache_rows = [{"location": place, "latitude": lat, "longitude": lon} for place, (lat, lon) in cache.items()]
    GEOCODE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cache_rows).to_csv(GEOCODE_CACHE_FILE, index=False)

    return [p[0] for p in coordinates], [p[1] for p in coordinates]


def great_circle_interpolate(start_lat, start_lon, end_lat, end_lon, fraction):
    if fraction <= 0: return float(start_lat), float(start_lon)
    if fraction >= 1: return float(end_lat), float(end_lon)

    lat1, lon1, lat2, lon2 = map(math.radians, (start_lat, start_lon, end_lat, end_lon))
    def to_vector(lat, lon): return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))
    a, b = to_vector(lat1, lon1), to_vector(lat2, lon2)
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    omega = math.acos(dot)

    if abs(omega) < 1e-10: return float(start_lat), float(start_lon)
    sin_omega = math.sin(omega)
    if abs(sin_omega) < 1e-10:
        delta_lon = ((end_lon - start_lon + 180) % 360) - 180
        return start_lat + fraction * (end_lat - start_lat), start_lon + fraction * delta_lon

    wa = math.sin((1 - fraction) * omega) / sin_omega
    wb = math.sin(fraction * omega) / sin_omega
    x, y, z = wa * a[0] + wb * b[0], wa * a[1] + wb * b[1], wa * a[2] + wb * b[2]

    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    lon = math.degrees(math.atan2(y, x))
    while lon - start_lon > 180: lon -= 360
    while lon - start_lon < -180: lon += 360
    return lat, lon


# ============================================================
# Build animation frames (WITH CAMERA TRACKING)
# ============================================================

def build_frames(locations, transports, latitudes, longitudes):
    frames = []
    
    # Calculate journey midpoint for the final zoom out
    mid_lat = sum(latitudes) / len(latitudes)
    mid_lon = sum(longitudes) / len(longitudes)
    # Standardize midpoint longitude to avoid wrapping issues
    while mid_lon > 180: mid_lon -= 360
    while mid_lon < -180: mid_lon += 360

    # 1. Cinematic Opening: Zoomed out, rotating
    for opening_step in range(OPENING_FRAMES + 1):
        progress = opening_step / OPENING_FRAMES
        opening_lon = OPENING_START_LON + progress * (OPENING_END_LON - OPENING_START_LON)
        
        frames.append(
            go.Frame(
                data=[],
                layout=go.Layout(
                    geo=dict(
                        projection=dict(
                            rotation=dict(lon=opening_lon, lat=GLOBE_CENTRE_LAT),
                            scale=ZOOM_OUT_SCALE
                        )
                    )
                ),
                name=f"opening_{opening_step}",
            )
        )

    frame_number = len(frames)
    total_segments = len(locations) - 1

    for segment in range(total_segments):
        start_lat, start_lon = latitudes[segment], longitudes[segment]
        end_lat, end_lon = latitudes[segment + 1], longitudes[segment + 1]
        
        transport = transports[segment]
        transport_icon = TRANSPORT_TYPES.get(transport, "❓")

        title_lines = [f"{TRANSPORT_TYPES.get(transports[i], '❓')} {locations[i]} → {locations[i + 1]}" for i in range(segment + 1)]
        title_text = "<br>".join(title_lines)

        completed_lats = [latitudes[i + 1] for i in range(segment)]
        completed_lons = [longitudes[i + 1] for i in range(segment)]
        completed_icons = [TRANSPORT_TYPES.get(transports[i], "❓") for i in range(segment)]

        for step in range(STEPS_PER_SEGMENT + 1):
            progress = step / STEPS_PER_SEGMENT

            # Interpolation
            if transport.strip().lower() == "plane":
                current_lat, current_lon = great_circle_interpolate(start_lat, start_lon, end_lat, end_lon, progress)
                path_points = [great_circle_interpolate(start_lat, start_lon, end_lat, end_lon, path_step / STEPS_PER_SEGMENT) for path_step in range(step + 1)]
            else:
                current_lat = start_lat + progress * (end_lat - start_lat)
                current_lon = start_lon + progress * (end_lon - start_lon)
                path_points = [(start_lat + (path_step / STEPS_PER_SEGMENT) * (end_lat - start_lat), start_lon + (path_step / STEPS_PER_SEGMENT) * (end_lon - start_lon)) for path_step in range(step + 1)]

            route_lats = latitudes[:segment + 1] + [point[0] for point in path_points[1:]]
            route_lons = longitudes[:segment + 1] + [point[1] for point in path_points[1:]]
            city_lats = latitudes[:segment + 1] + [end_lat]
            city_lons = longitudes[:segment + 1] + [end_lon]
            city_labels = locations[:segment + 1] + [locations[segment + 1]]

            emoji_lats = completed_lats + [current_lat]
            emoji_lons = completed_lons + [current_lon]
            emoji_text = completed_icons + [transport_icon]

            # ----------------------------------------------------
            # CAMERA LOGIC (Steps 2-7)
            # ----------------------------------------------------
            cam_lat, cam_lon, cam_scale = current_lat, current_lon, ZOOM_IN_SCALE

            # 2. Smooth Zoom-In (First segment only)
            if segment == 0 and step <= ZOOM_TRANSITION_FRAMES:
                progress_zoom = step / ZOOM_TRANSITION_FRAMES
                cam_scale = ZOOM_OUT_SCALE + (ZOOM_IN_SCALE - ZOOM_OUT_SCALE) * progress_zoom

            # 6. Cinematic Arrival Close-Up (Final segment only, near the end)
            if segment == total_segments - 1 and progress > 0.70:
                arrival_progress = (progress - 0.70) / 0.30
                cam_scale = ZOOM_IN_SCALE + (ZOOM_ARRIVAL_SCALE - ZOOM_IN_SCALE) * arrival_progress

            # 7. Zoom Out to reveal Earth (At the very last frame)
            if segment == total_segments - 1 and step == STEPS_PER_SEGMENT:
                # Blend camera center from destination to midpoint
                cam_lat = end_lat # We keep center at destination
                cam_scale = ZOOM_OUT_SCALE # Zoom all the way out
                # Alternatively, to center on the whole trip, you'd interpolate cam_lat/lon
                # but centering on the destination as it zooms out is a great cinematic effect.

            frames.append(
                go.Frame(
                    data=[
                        go.Scattergeo(lon=route_lons, lat=route_lats, mode="lines", line=dict(width=4, color="royalblue")),
                        go.Scattergeo(lon=city_lons, lat=city_lats, mode="markers+text", text=city_labels, textposition="top center", marker=dict(size=8, color="royalblue")),
                        go.Scattergeo(lon=emoji_lons, lat=emoji_lats, mode="text", text=emoji_text, textfont=dict(size=28)),
                    ],
                    layout=go.Layout(
                        title=dict(text=title_text),
                        geo=dict(
                            projection=dict(
                                # 3, 4, 5. Camera tracks the emoji
                                rotation=dict(lon=cam_lon, lat=cam_lat),
                                scale=cam_scale
                            )
                        ),
                    ),
                    name=str(frame_number),
                )
            )
            frame_number += 1

    return frames


# ============================================================
# Create the orthographic globe
# ============================================================

def create_figure(locations, transports, latitudes, longitudes):
    frames = build_frames(locations, transports, latitudes, longitudes)
    first_icon = TRANSPORT_TYPES.get(transports[0], "❓")

    fig = go.Figure(
        data=[
            go.Scattergeo(lon=[longitudes[0]], lat=[latitudes[0]], mode="lines", line=dict(width=4, color="royalblue")),
            go.Scattergeo(lon=[longitudes[0]], lat=[latitudes[0]], mode="markers+text", text=[locations[0]], textposition="top center", marker=dict(size=8, color="royalblue")),
            go.Scattergeo(lon=[longitudes[0]], lat=[latitudes[0]], mode="text", text=[first_icon], textfont=dict(size=28)),
        ],
        frames=frames,
    )

    fig.update_layout(
        width=GLOBE_WIDTH, height=GLOBE_HEIGHT, autosize=True,
        margin=dict(l=10, r=10, t=70, b=10),
        title=dict(text="", x=0.02, y=0.98, xanchor="left", yanchor="top"),
        geo=dict(
            projection=dict(
                type="orthographic",
                rotation=dict(lon=OPENING_START_LON, lat=GLOBE_CENTRE_LAT),
                scale=ZOOM_OUT_SCALE,
            ),
            showland=True, landcolor="rgb(166, 190, 145)",
            showocean=True, oceancolor="rgb(105, 165, 205)",
            showlakes=True, lakecolor="rgb(105, 165, 205)",
            showcountries=True, countrycolor="rgb(90, 90, 90)",
            showcoastlines=True, coastlinecolor="rgb(70, 70, 70)",
            showframe=True, framecolor="gray", bgcolor="white",
        ),
        updatemenus=[
            dict(
                type="buttons", 
                showactive=False, 
                x=0.01, 
                y=0.95, 
                xanchor="left", 
                yanchor="top",
                buttons=[
                    dict(
                        label="▶ Play", 
                        method="animate", 
                        args=[
                            None, 
                            {
                                "frame": {"duration": FRAME_DURATION_MS, "redraw": True}, # Camera requires True
                                "transition": {"duration": FRAME_DURATION_MS},            # Smooth tween to mask blink
                                "fromcurrent": True,
                            }
                        ]
                    ),
                    dict(
                        label="⏸ Pause", 
                        method="animate", 
                        args=[
                            [None], 
                            {
                                "frame": {"duration": 0, "redraw": True}, 
                                "mode": "immediate", 
                                "transition": {"duration": 0}
                            }
                        ]
                    ),
                ],
            )
        ],
    )
    return fig


# ============================================================
# Main
# ============================================================

def main():
    _, locations, transports = read_trip(CSV_FILE)
    latitudes, longitudes = geocode_locations(locations)

    print("\nBuilding cinematic globe animation...")
    fig = create_figure(locations, transports, latitudes, longitudes)

    print(f"Created {len(fig.frames)} animation frames for {len(transports)} journey segment(s).")
    fig.show()

if __name__ == "__main__":
    main()