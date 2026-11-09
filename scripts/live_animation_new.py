
import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time
import math

# =====================================================
# TRANSPORT TYPES
# =====================================================

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
    "Donkey": "🫏"
}


# =====================================================
# CITY / COUNTRY MAPPING
# =====================================================

CITY_COUNTRIES = {
    "Sydney": ("Sydney, Australia", "au"),
    "Canberra": ("Canberra, Australia", "au"),
    "Melbourne": ("Melbourne, Australia", "au"),
    "Devonport": ("Devonport, Tasmania, Australia", "au"),
    "Hobart": ("Hobart, Tasmania, Australia", "au"),
    "Strahan": ("Strahan, Tasmania, Australia", "au"),
    "Los Angeles": ("Los Angeles, California, USA", "us")
}


# =====================================================
# READ TRIP DATA
# =====================================================

trip = pd.read_csv("data/trip.csv")

if trip.empty:
    raise ValueError("Trip CSV file is empty.")

required_columns = ["Date", "From", "To", "Transport"]

for column in required_columns:
    if column not in trip.columns:
        raise ValueError(f"Missing required column: {column}")

locations = [trip.iloc[0]["From"]] + trip["To"].tolist()
transports = trip["Transport"].tolist()

if len(locations) != len(transports) + 1:
    raise ValueError("Invalid trip route data.")


# =====================================================
# GEOCODING
# =====================================================

geo = Nominatim(
    user_agent="travel_documentary_generator",
    timeout=10
)

latitudes = []
longitudes = []

print("\nGetting coordinates...\n")

for city in locations:

    if city not in CITY_COUNTRIES:
        raise ValueError(
            f"City '{city}' is missing from CITY_COUNTRIES."
        )

    search_name, country_code = CITY_COUNTRIES[city]

    location = geo.geocode(
        search_name,
        country_codes=country_code,
        exactly_one=True
    )

    if location is None:
        raise ValueError(
            f"Could not find coordinates for {city}"
        )

    lat = location.latitude
    lon = location.longitude

    latitudes.append(lat)
    longitudes.append(lon)

    print(f"{city}: {lat}, {lon}")

    time.sleep(1)


# =====================================================
# GREAT-CIRCLE INTERPOLATION
# =====================================================

def great_circle_points(
    lat1, lon1, lat2, lon2, steps=50
):

    # Convert coordinates to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Convert coordinates to 3D Cartesian vectors
    def to_vector(lat, lon):
        return (
            math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat)
        )

    v1 = to_vector(lat1, lon1)
    v2 = to_vector(lat2, lon2)

    # Angular distance
    dot = sum(a * b for a, b in zip(v1, v2))
    dot = max(-1.0, min(1.0, dot))

    omega = math.acos(dot)

    points = []

    for i in range(steps + 1):

        fraction = i / steps

        if omega < 1e-10:

            lat = lat1 + fraction * (lat2 - lat1)
            lon = lon1 + fraction * (lon2 - lon1)

        else:

            sin_omega = math.sin(omega)

            a = math.sin((1 - fraction) * omega) / sin_omega
            b = math.sin(fraction * omega) / sin_omega

            x = a * v1[0] + b * v2[0]
            y = a * v1[1] + b * v2[1]
            z = a * v1[2] + b * v2[2]

            lat = math.atan2(
                z,
                math.sqrt(x * x + y * y)
            )

            lon = math.atan2(y, x)

        # Convert back to degrees
        lat = math.degrees(lat)
        lon = math.degrees(lon)

        # Normalize longitude
        lon = (lon + 180) % 360 - 180

        points.append((lat, lon))

    return points


# =====================================================
# MAP BOUNDS
# =====================================================

all_route_lats = []

for segment in range(len(locations) - 1):

    points = great_circle_points(
        latitudes[segment],
        longitudes[segment],
        latitudes[segment + 1],
        longitudes[segment + 1],
        steps=100
    )

    all_route_lats.extend([p[0] for p in points])


padding_lat = 8

min_lat = max(-90, min(all_route_lats) - padding_lat)
max_lat = min(90, max(all_route_lats) + padding_lat)


# =====================================================
# BUILD ANIMATION FRAMES
# =====================================================

frames = []

steps_per_segment = 50
frame_number = 0

for segment in range(len(locations) - 1):

    start_lat = latitudes[segment]
    start_lon = longitudes[segment]

    end_lat = latitudes[segment + 1]
    end_lon = longitudes[segment + 1]

    transport = transports[segment]

    transport_icon = TRANSPORT_TYPES.get(
        transport, "❓"
    )

    # Calculate complete great-circle path
    segment_points = great_circle_points(
        start_lat,
        start_lon,
        end_lat,
        end_lon,
        steps=steps_per_segment
    )

    segment_lats = [p[0] for p in segment_points]
    segment_lons = [p[1] for p in segment_points]

    # Accumulated trip title
    title_lines = []

    for i in range(segment + 1):

        icon = TRANSPORT_TYPES.get(
            transports[i], "❓"
        )

        title_lines.append(
            f"{icon} {locations[i]} → {locations[i + 1]}"
        )

    title_text = "<br>".join(title_lines)

    # Completed transport icons
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

    # Create animation frames
    for step in range(steps_per_segment + 1):

        # Current position along great-circle path
        current_lat = segment_lats[step]
        current_lon = segment_lons[step]

        # Historical route + current route
        route_lats = (
            latitudes[:segment + 1]
            + segment_lats[1:step + 1]
        )

        route_lons = (
            longitudes[:segment + 1]
            + segment_lons[1:step + 1]
        )

        # City labels only at actual destinations
        city_labels = (
            locations[:segment + 1]
            + [None] * (len(route_lats) - segment - 1)
        )

        if step == steps_per_segment:
            city_labels[-1] = locations[segment + 1]

        # Transport emoji positions
        emoji_lats = completed_lats + [current_lat]
        emoji_lons = completed_lons + [current_lon]

        emoji_text = completed_icons + [transport_icon]

        frames.append(
            go.Frame(
                data=[
                    # Trace 0: route and city labels
                    go.Scattergeo(
                        lon=route_lons,
                        lat=route_lats,
                        mode="lines+markers+text",
                        text=city_labels,
                        textposition="top center",
                        line=dict(
                            width=4,
                            color="royalblue"
                        ),
                        marker=dict(
                            size=6,
                            color="royalblue"
                        )
                    ),

                    # Trace 1: transport emojis
                    go.Scattergeo(
                        lon=emoji_lons,
                        lat=emoji_lats,
                        mode="text",
                        text=emoji_text,
                        textfont=dict(size=28)
                    )
                ],
                layout=go.Layout(
                    title=title_text
                ),
                name=str(frame_number)
            )
        )

        frame_number += 1


# =====================================================
# INITIAL FIGURE
# =====================================================

initial_icon = TRANSPORT_TYPES.get(
    transports[0], "❓"
)

fig = go.Figure(
    data=[

        # Trace 0: starting location
        go.Scattergeo(
            lon=[longitudes[0]],
            lat=[latitudes[0]],
            mode="lines+markers+text",
            text=[locations[0]],
            textposition="top center",
            line=dict(
                width=4,
                color="royalblue"
            ),
            marker=dict(
                size=8,
                color="royalblue"
            )
        ),

        # Trace 1: starting transport emoji
        go.Scattergeo(
            lon=[longitudes[0]],
            lat=[latitudes[0]],
            mode="text",
            text=[initial_icon],
            textfont=dict(size=28)
        )
    ],
    frames=frames
)


# =====================================================
# LAYOUT
# =====================================================

fig.update_layout(

    width=1400,
    height=900,
    autosize=True,

    margin=dict(
        l=0,
        r=0,
        t=40,
        b=0
    ),

    title=dict(
        text="",
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top"
    ),

    geo=dict(

        projection=dict(
            type="natural earth",
            rotation=dict(lon=180)
        ),

        showland=True,
        showcountries=True,
        showocean=True,
        oceancolor="rgb(225, 238, 250)",

        lataxis=dict(
            range=[min_lat, max_lat]
        ),

        # Full longitude range allows the Pacific route
        # to be displayed across the International Date Line.
        lonaxis=dict(
            range=[-180, 180]
        ),

        domain=dict(
            x=[0, 1],
            y=[0, 1]
        )
    ),

    updatemenus=[

        dict(
            type="buttons",
            x=0.02,
            y=0.75,

            buttons=[

                dict(
                    label="▶ Play",
                    method="animate",

                    args=[
                        None,
                        {
                            "frame": {
                                "duration": 100,
                                "redraw": True
                            },
                            "transition": {
                                "duration": 0
                            },
                            "fromcurrent": True
                        }
                    ]
                ),

                dict(
                    label="⏸ Pause",
                    method="animate",

                    args=[
                        [None],
                        {
                            "frame": {
                                "duration": 0,
                                "redraw": False
                            },
                            "mode": "immediate",
                            "transition": {
                                "duration": 0
                            }
                        }
                    ]
                )
            ]
        )
    ]
)


# =====================================================
# DISPLAY
# =====================================================

fig.show()
