import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from collections import defaultdict
import time

# -----------------------------
# Transport Types
# -----------------------------
TRANSPORT_TYPES = {
    "Walking": "🚶", "Bicycle": "🚲", "Motorbike": "🏍️", "Car": "🚗",
    "Bus": "🚌", "Train": "🚆", "Plane": "✈️", "Helicopter": "🚁",
    "Drone": "🛸", "Ship": "🚢", "Boat": "⛵", "Swimming": "🏊",
    "Horse": "🐎", "Camel": "🐪", "Donkey": "🫏",
				  
					
					  
						 
					
				   
				  
					   
					
					
					
}

# -----------------------------
# Read trip
# -----------------------------
trip = pd.read_csv("data/trip.csv")

locations = [trip.iloc[0]["From"]]
for _, row in trip.iterrows():
    locations.append(row["To"])

transports = trip["Transport"].tolist()

# -----------------------------
# Geocode
# -----------------------------
geo = Nominatim(user_agent="travel_documentary_generator", timeout=10)

			  
			   

latitudes, longitudes = [], []
print("Getting coordinates...")
for city in locations:
    loc = geo.geocode(f"{city} Australia")
    latitudes.append(loc.latitude)
    longitudes.append(loc.longitude)
    print(f"{city}: {loc.latitude}, {loc.longitude}")
    time.sleep(1)

# -----------------------------
# Map bounds
# -----------------------------
			   
padding_lat, padding_lon = 1, 1
min_lat = min(latitudes) - padding_lat
max_lat = max(latitudes) + padding_lat
min_lon = min(longitudes) - padding_lon
max_lon = max(longitudes) + padding_lon

# -----------------------------
# Build frames
# -----------------------------
frames = []
steps_per_segment = 50
frame_number = 0

for segment in range(len(locations) - 1):
    start_lat, start_lon = latitudes[segment], longitudes[segment]
								   
    end_lat, end_lon     = latitudes[segment + 1], longitudes[segment + 1]
									 

    transport            = transports[segment]
    transport_icon       = TRANSPORT_TYPES.get(transport, "❓")

    # Title: accumulate legs so far
    title_lines = []
    for i in range(segment + 1):
        icon = TRANSPORT_TYPES.get(transports[i], "❓")
        title_lines.append(f"{icon} {locations[i]} → {locations[i + 1]}")
    title_text = "<br>".join(title_lines)

    # Group completed legs by ENDPOINT city, then spread per-city
    parked = defaultdict(list)
    for i in range(segment):
        endpoint = locations[i + 1]
					   
        parked[endpoint].append(TRANSPORT_TYPES.get(transports[i], "❓"))
	 

    # Precompute final offsets (do once per segment, not per frame)
    parked_positions = []   # list of (lat, lon, icon)
    SPREAD = 0.18
    for city, icons in parked.items():
        idx = locations.index(city)          # first occurrence is fine here
        base_lat, base_lon = latitudes[idx], longitudes[idx]
        n = len(icons)
        for j, icon in enumerate(icons):
            offset = (j - (n - 1) / 2) * SPREAD
            parked_positions.append((base_lat, base_lon + offset, icon))

    for step in range(steps_per_segment + 1):
        progress = step / steps_per_segment

        current_lat = start_lat + progress * (end_lat - start_lat)
        current_lon = start_lon + progress * (end_lon - start_lon)

        route_lats = latitudes[:segment + 1] + [current_lat]
        route_lons = longitudes[:segment + 1] + [current_lon]
        city_labels = locations[:segment + 1] + [locations[segment + 1]]

        emoji_lats = [p[0] for p in parked_positions] + [current_lat]
												   
        emoji_lons = [p[1] for p in parked_positions] + [current_lon]
        emoji_text = [p[2] for p in parked_positions] + [transport_icon]

        frames.append(
            go.Frame(
                data=[
														
                    go.Scattergeo(
                        lon=route_lons, lat=route_lats,
									   
                        mode="lines+markers+text",
										 
                        text=city_labels, textposition="top center",
                        line=dict(width=4, color="royalblue"),
                        marker=dict(size=8, color="royalblue"),
                    ),
														   
                    go.Scattergeo(
                        lon=emoji_lons, lat=emoji_lats,
									   
									
                        mode="text", text=emoji_text,
                        textfont=dict(size=28),
                    ),
                ],
                layout=go.Layout(
                    title=dict(text=title_text),
                ),
                name=str(frame_number),
            )
        )
        frame_number += 1

# -----------------------------
# Initial figure
# -----------------------------

initial_icon = TRANSPORT_TYPES.get(transports[0], "❓")
																	 
				  

fig = go.Figure(
    data=[
        go.Scattergeo(
            lon=[longitudes[0]], lat=[latitudes[0]],
							   
            mode="lines+markers+text",
								
            text=[locations[0]], textposition="top center",
            line=dict(width=4, color="royalblue"),
            marker=dict(size=8, color="royalblue"),
        ),
        go.Scattergeo(
            lon=[longitudes[0]], lat=[latitudes[0]],
							   
						
            mode="text", text=[initial_icon],
            textfont=dict(size=28),
        ),
    ],
    frames=frames,
)

# -----------------------------
# Layout
# -----------------------------
fig.update_layout(
    # Legs text as a semi-transparent annotation on the LEFT
    title=dict(text="", x=0.01, y=0.99),  # keep layout title empty
    annotations=[
        dict(
            text="",                          # will be updated per frame below
            xref="paper", yref="paper",
            x=0.01, y=0.99,
			   
            xanchor="left", yanchor="top",
            showarrow=False,
            align="left",
            font=dict(size=15, family="Arial"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            borderpad=8,
        )
    ],
    geo=dict(
        projection_type="natural earth",
					  
        showland=True, showcountries=True,
        lataxis=dict(range=[min_lat, max_lat]),
        lonaxis=dict(range=[min_lon, max_lon]),
    ),
    # Play button: bottom-right of the FIGURE (not plot area)
    updatemenus=[
        dict(
            type="buttons",
            direction="left",
            x=0.98, y=0.02,
            xanchor="right", yanchor="bottom",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
						  
							 
						 
                    args=[None, {"frame": {"duration": 100, "redraw": True},
                                 "fromcurrent": True}],
						  
					  
                )
            ],
        )
    ],
)

# -----------------------------
# Bake title text into EVERY frame's annotation
# (Plotly frames can override layout.annotations per frame)
# -----------------------------
for i, frame in enumerate(fig.frames):
    # Which segment does this frame belong to?
    seg = i // (steps_per_segment + 1)
    lines = []
    for k in range(seg + 1):
        icon = TRANSPORT_TYPES.get(transports[k], "❓")
        lines.append(f"{icon} {locations[k]} → {locations[k + 1]}")
    frame.layout.annotations = (
        dict(
            text="<br>".join(lines),
            xref="paper", yref="paper",
            x=0.01, y=0.99,
            xanchor="left", yanchor="top",
            showarrow=False,
            align="left",
            font=dict(size=15, family="Arial"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            borderpad=8,
        ),
    )

fig.show()