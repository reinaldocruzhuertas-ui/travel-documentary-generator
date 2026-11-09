# Future enhancement:
# 1.	Dramatic opening shots of the Earth.
# 2.	Smooth zoom-in and zoom-out animations.
# 3.	Camera tracking that follows the moving transport.
# 4.	Cinematic destination arrivals.
# 5.	Beautiful transitions between journeys.


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
# 180 degrees centres the Pacific, keeping Sydney and Los Angeles
# on the visible side of the globe.
GLOBE_CENTRE_LON = 180
GLOBE_CENTRE_LAT = 0

STEPS_PER_SEGMENT = 50
FRAME_DURATION_MS = 100
GLOBE_WIDTH = 1400
GLOBE_HEIGHT = 900

# Cinematic Step 1: opening Earth reveal.
# Rotate from a Greenwich/Europe-Africa-facing view to the existing Pacific-facing view.
OPENING_FRAMES = 36
OPENING_START_LON = 0
OPENING_END_LON = GLOBE_CENTRE_LON

TRANSPORT_TYPES = {
    "Walking": "🚶",
    "Bicycle": "🚲",
    "Motorbike": "🏍️",
    "Car": "🚗",
    "Bus": "🚌",
    "Train": "🚆",
    "Plane": "✈️",
    "Helicopter": "🚁",
    "Drone": "🛸",
    "Ship": "🚢",
    "Boat": "⛵",
    "Swimming": "🏊",
    "Horse": "🐎",
    "Camel": "🐪",
    "Donkey": "🫏",
}


# ============================================================
# Read and validate trip data
# ============================================================

def read_trip(csv_file: Path):
    if not csv_file.exists():
        raise FileNotFoundError(
            f"Trip file not found: {csv_file.resolve()}\n"
            "Expected columns: From, To, Transport"
        )

    trip = pd.read_csv(csv_file)

    required_columns = {"From", "To", "Transport"}
    missing = required_columns.difference(trip.columns)
    if missing:
        raise ValueError(
            "Missing CSV column(s): " + ", ".join(sorted(missing))
        )

    if trip.empty:
        raise ValueError("The trip.csv file contains no journeys.")

    for column in required_columns:
        trip[column] = trip[column].astype("string").str.strip()

    if trip[["From", "To", "Transport"]].isna().any().any():
        raise ValueError("From, To and Transport cannot contain blank values.")

    if (trip[["From", "To", "Transport"]] == "").any().any():
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
                cache[str(row["location"])] = (
                    float(row["latitude"]),
                    float(row["longitude"]),
                )
        except (KeyError, ValueError, pd.errors.ParserError):
            print("Warning: geocode cache could not be read; rebuilding it.")

    geo = Nominatim(
        user_agent="live_animation_global_travel_visualizer",
        timeout=20,
    )

    # Respect Nominatim's public service usage policy (at least 1 second
    # between requests). Cached locations do not require another request.
    geocode = RateLimiter(
        geo.geocode,
        min_delay_seconds=1.1,
        swallow_exceptions=False,
        return_value_on_exception=None,
    )

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
                raise ValueError(
                    f"Could not find '{place}'. Add its country to the "
                    "location in trip.csv, e.g. 'Paris, France'."
                )

            lat, lon = float(result.latitude), float(result.longitude)
            cache[place] = (lat, lon)
            new_cache_entries.append(
                {"location": place, "latitude": lat, "longitude": lon}
            )
            print(f"         {lat:.6f}, {lon:.6f}")

        coordinates.append((lat, lon))

    # Save all known coordinates so future runs are faster and make
    # fewer requests to the geocoding service.
    cache_rows = [
        {"location": place, "latitude": lat, "longitude": lon}
        for place, (lat, lon) in cache.items()
    ]
    GEOCODE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cache_rows).to_csv(GEOCODE_CACHE_FILE, index=False)

    latitudes = [point[0] for point in coordinates]
    longitudes = [point[1] for point in coordinates]
    return latitudes, longitudes



def great_circle_interpolate(start_lat, start_lon, end_lat, end_lon, fraction):
    """
    Return a point along the shortest great-circle arc between two
    coordinates using spherical linear interpolation (slerp).

    The returned longitude is kept continuous relative to start_lon.
    For example, Sydney (151 E) to Los Angeles (118 W) travels east
    through longitudes greater than 180, rather than west through
    almost 270 degrees.
    """
    if fraction <= 0:
        return float(start_lat), float(start_lon)
    if fraction >= 1:
        end_unwrapped_lon = float(end_lon)
        while end_unwrapped_lon - start_lon > 180:
            end_unwrapped_lon -= 360
        while end_unwrapped_lon - start_lon < -180:
            end_unwrapped_lon += 360
        return float(end_lat), end_unwrapped_lon

    lat1, lon1, lat2, lon2 = map(
        math.radians, (start_lat, start_lon, end_lat, end_lon)
    )

    def to_vector(lat, lon):
        return (
            math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat),
        )

    a = to_vector(lat1, lon1)
    b = to_vector(lat2, lon2)

    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    omega = math.acos(dot)

    if abs(omega) < 1e-10:
        return float(start_lat), float(start_lon)

    sin_omega = math.sin(omega)
    if abs(sin_omega) < 1e-10:
        # Nearly antipodal points have no unique shortest great circle.
        # Fall back to the shortest-longitude linear interpolation.
        delta_lon = ((end_lon - start_lon + 180) % 360) - 180
        lat = start_lat + fraction * (end_lat - start_lat)
        lon = start_lon + fraction * delta_lon
        return lat, lon

    wa = math.sin((1 - fraction) * omega) / sin_omega
    wb = math.sin(fraction * omega) / sin_omega
    x = wa * a[0] + wb * b[0]
    y = wa * a[1] + wb * b[1]
    z = wa * a[2] + wb * b[2]

    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    lon = math.degrees(math.atan2(y, x))

    # Unwrap longitude so it progresses continuously across +/-180.
    while lon - start_lon > 180:
        lon -= 360
    while lon - start_lon < -180:
        lon += 360

    return lat, lon

# ============================================================
# Build animation frames
# ============================================================

def build_frames(locations, transports, latitudes, longitudes):
    frames = []
    frame_number = 0

    # Cinematic Step 1: slowly reveal the Earth before the journey begins.
    # This changes only the camera orientation; route calculations remain
    # exactly as they were in the working version.
    for opening_step in range(OPENING_FRAMES + 1):
        progress = opening_step / OPENING_FRAMES
        opening_lon = (
            OPENING_START_LON
            + progress * (OPENING_END_LON - OPENING_START_LON)
        )

        frames.append(
            go.Frame(
                data=[],
                layout=go.Layout(
                    geo=dict(
                        projection=dict(
                            rotation=dict(
                                lon=opening_lon,
                                lat=GLOBE_CENTRE_LAT,
                            )
                        )
                    )
                ),
                name=f"opening_{opening_step}",
            )
        )

    frame_number = len(frames)

    for segment in range(len(locations) - 1):
        start_lat = latitudes[segment]
        start_lon = longitudes[segment]
        end_lat = latitudes[segment + 1]
        end_lon = longitudes[segment + 1]

        transport = transports[segment]
        transport_icon = TRANSPORT_TYPES.get(transport, "❓")

        title_lines = []
        for i in range(segment + 1):
            icon = TRANSPORT_TYPES.get(transports[i], "❓")
            title_lines.append(
                f"{icon} {locations[i]} → {locations[i + 1]}"
            )
        title_text = "<br>".join(title_lines)

        # Park completed transport icons at their destination cities.
        completed_lats = [
            latitudes[i + 1] for i in range(segment)
        ]
        completed_lons = [
            longitudes[i + 1] for i in range(segment)
        ]
        completed_icons = [
            TRANSPORT_TYPES.get(transports[i], "❓")
            for i in range(segment)
        ]

        for step in range(STEPS_PER_SEGMENT + 1):
            progress = step / STEPS_PER_SEGMENT

            # Aircraft follow the shortest great-circle path. Other
            # transport types retain the original linear animation.
            if transport.strip().lower() == "plane":
                current_lat, current_lon = great_circle_interpolate(
                    start_lat, start_lon, end_lat, end_lon, progress
                )
                path_points = [
                    great_circle_interpolate(
                        start_lat, start_lon, end_lat, end_lon,
                        path_step / STEPS_PER_SEGMENT
                    )
                    for path_step in range(step + 1)
                ]
            else:
                current_lat = start_lat + progress * (end_lat - start_lat)
                current_lon = start_lon + progress * (end_lon - start_lon)
                path_points = [
                    (
                        start_lat + (path_step / STEPS_PER_SEGMENT)
                        * (end_lat - start_lat),
                        start_lon + (path_step / STEPS_PER_SEGMENT)
                        * (end_lon - start_lon),
                    )
                    for path_step in range(step + 1)
                ]

            # Draw the complete route so far, including the sampled
            # curved flight path for aircraft.
            route_lats = latitudes[:segment + 1] + [
                point[0] for point in path_points[1:]
            ]
            route_lons = longitudes[:segment + 1] + [
                point[1] for point in path_points[1:]
            ]

            # Keep city labels/markers separate from the route line so
            # intermediate flight-path points do not create extra markers.
            city_lats = latitudes[:segment + 1] + [end_lat]
            city_lons = longitudes[:segment + 1] + [end_lon]
            city_labels = locations[:segment + 1] + [
                locations[segment + 1]
            ]

            emoji_lats = completed_lats + [current_lat]
            emoji_lons = completed_lons + [current_lon]
            emoji_text = completed_icons + [transport_icon]

            frames.append(
                go.Frame(
                    data=[
                        go.Scattergeo(
                            lon=route_lons,
                            lat=route_lats,
                            mode="lines",
                            line=dict(width=4, color="royalblue"),
                        ),
                        go.Scattergeo(
                            lon=city_lons,
                            lat=city_lats,
                            mode="markers+text",
                            text=city_labels,
                            textposition="top center",
                            marker=dict(size=8, color="royalblue"),
                        ),
                        go.Scattergeo(
                            lon=emoji_lons,
                            lat=emoji_lats,
                            mode="text",
                            text=emoji_text,
                            textfont=dict(size=28),
                        ),
                    ],
                    layout=go.Layout(
                        title=dict(text=title_text),
                        geo=dict(
                            projection=dict(
                                rotation=dict(
                                    lon=GLOBE_CENTRE_LON,
                                    lat=GLOBE_CENTRE_LAT,
                                )
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
    frames = build_frames(
        locations, transports, latitudes, longitudes
    )

    first_icon = TRANSPORT_TYPES.get(transports[0], "❓")

    fig = go.Figure(
        data=[
            go.Scattergeo(
                lon=[longitudes[0]],
                lat=[latitudes[0]],
                mode="lines",
                line=dict(width=4, color="royalblue"),
            ),
            go.Scattergeo(
                lon=[longitudes[0]],
                lat=[latitudes[0]],
                mode="markers+text",
                text=[locations[0]],
                textposition="top center",
                marker=dict(size=8, color="royalblue"),
            ),
            go.Scattergeo(
                lon=[longitudes[0]],
                lat=[latitudes[0]],
                mode="text",
                text=[first_icon],
                textfont=dict(size=28),
            ),
        ],
        frames=frames,
    )

    fig.update_layout(
        width=GLOBE_WIDTH,
        height=GLOBE_HEIGHT,
        autosize=True,
        margin=dict(l=10, r=10, t=70, b=10),

        title=dict(
            text="",
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
        ),

        # TRUE SPHERICAL VIEW:
        # Orthographic projection displays only the visible hemisphere.
        geo=dict(
            projection=dict(
                type="orthographic",
                rotation=dict(
                    lon=OPENING_START_LON,
                    lat=GLOBE_CENTRE_LAT,
                ),
                scale=1,
            ),
            showland=True,
            # landcolor="rgb(240, 220, 150)",
            landcolor="rgb(166, 190, 145)",
            showocean=True,
            # oceancolor="white",
            oceancolor="rgb(105, 165, 205)",
            showlakes=True,
            lakecolor="rgb(105, 165, 205)",            
            showcountries=True,
            countrycolor="rgb(90, 90, 90)",
            showcoastlines=True,
            coastlinecolor="rgb(70, 70, 70)",
            showframe=True,
            framecolor="gray",
            bgcolor="white",
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
                                "frame": {
                                    "duration": FRAME_DURATION_MS,
                                    "redraw": True,
                                },
                                "transition": {"duration": 0},
                                "fromcurrent": True,
                            },
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
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

    print("Locations:")
    for place in locations:
        print(f"  - {place}")

    latitudes, longitudes = geocode_locations(locations)

    print("\nBuilding globe animation...")
    fig = create_figure(
        locations, transports, latitudes, longitudes
    )

    print(
        f"Created {len(fig.frames)} animation frames "
        f"for {len(transports)} journey segment(s)."
    )
    print("Globe projection:", fig.layout.geo.projection.type)
    print(
        "Globe centre:",
        GLOBE_CENTRE_LON,
        GLOBE_CENTRE_LAT,
    )

    fig.show()


if __name__ == "__main__":
    main()
