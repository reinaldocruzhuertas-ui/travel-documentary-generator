# Minimal test: does Scattermap support smooth camera tracking (no blinking)?
# Run this, press Play, and observe:
#   - Does the marker move smoothly?
#   - Does the camera follow the marker?
#   - Is there white blinking between frames?

import math
import plotly.graph_objects as go

# -----------------------------
# Test route (3 cities)
# -----------------------------
CITIES = [
    {"name": "Sydney",    "lat": -33.8688, "lon": 151.2093, "icon": "🚗"},
    {"name": "Canberra",  "lat": -35.2809, "lon": 149.1300, "icon": "🚲"},
    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631, "icon": "✈️"},
]

STEPS_PER_SEGMENT = 50
FRAME_DURATION_MS = 100
ZOOM_TRACK = 6   # MapLibre zoom level while tracking

# -----------------------------
# Build frames
# -----------------------------
frames = []
frame_number = 0
total_segments = len(CITIES) - 1

for segment in range(total_segments):
    start = CITIES[segment]
    end = CITIES[segment + 1]

    for step in range(STEPS_PER_SEGMENT + 1):
        p = step / STEPS_PER_SEGMENT
        cur_lat = start["lat"] + p * (end["lat"] - start["lat"])
        cur_lon = start["lon"] + p * (end["lon"] - start["lon"])

        # Route line so far
        route_lats = [c["lat"] for c in CITIES[:segment + 1]] + [cur_lat]
        route_lons = [c["lon"] for c in CITIES[:segment + 1]] + [cur_lon]

        # City labels
        city_lats = [c["lat"] for c in CITIES[:segment + 1]] + [end["lat"]]
        city_lons = [c["lon"] for c in CITIES[:segment + 1]] + [end["lon"]]
        city_names = [c["name"] for c in CITIES[:segment + 1]] + [end["name"]]

        # Moving emoji
        emoji_lats = [cur_lat]
        emoji_lons = [cur_lon]
        emoji_text = [end["icon"]]

        frames.append(
            go.Frame(
                data=[
                    go.Scattermap(
                        lon=route_lons, lat=route_lats,
                        mode="lines",
                        line=dict(width=4, color="royalblue"),
                    ),
                    go.Scattermap(
                        lon=city_lons, lat=city_lats,
                        mode="markers+text",
                        text=city_names,
                        textposition="top center",
                        marker=dict(size=8, color="royalblue"),
                    ),
                    go.Scattermap(
                        lon=emoji_lons, lat=emoji_lats,
                        mode="text",
                        text=emoji_text,
                        textfont=dict(size=32),
                    ),
                ],
                layout=go.Layout(
                    map=dict(
                        center=dict(lat=cur_lat, lon=cur_lon),
                        zoom=ZOOM_TRACK,
                    ),
                    title=dict(text=f"{start['name']} → {end['name']} ({int(p*100)}%)"),
                ),
                name=str(frame_number),
            )
        )
        frame_number += 1

# -----------------------------
# Initial figure (must match trace structure)
# -----------------------------
fig = go.Figure(
    data=[
        go.Scattermap(
            lon=[CITIES[0]["lon"]], lat=[CITIES[0]["lat"]],
            mode="lines", line=dict(width=4, color="royalblue"),
        ),
        go.Scattermap(
            lon=[CITIES[0]["lon"]], lat=[CITIES[0]["lat"]],
            mode="markers+text",
            text=[CITIES[0]["name"]],
            textposition="top center",
            marker=dict(size=8, color="royalblue"),
        ),
        go.Scattermap(
            lon=[CITIES[0]["lon"]], lat=[CITIES[0]["lat"]],
            mode="text",
            text=[CITIES[0]["icon"]],
            textfont=dict(size=32),
        ),
    ],
    frames=frames,
)

# -----------------------------
# Layout
# -----------------------------
fig.update_layout(
    autosize=True,
    margin=dict(l=0, r=0, t=60, b=0),
    title=dict(text="Scattermap Camera Tracking Test", x=0.02, y=0.97,
               xanchor="left", yanchor="top", font=dict(size=14)),
    map=dict(
        style="carto-voyager",   # clean, fast, no token
        center=dict(lat=CITIES[0]["lat"], lon=CITIES[0]["lon"]),
        zoom=ZOOM_TRACK,
    ),
    updatemenus=[
        dict(
            type="buttons", showactive=False,
            x=0.01, y=0.95, xanchor="left", yanchor="top",
            buttons=[
                dict(
                    label="▶ Play", method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": FRAME_DURATION_MS, "redraw": True},
                            "transition": {"duration": 0},
                            "fromcurrent": True,
                        },
                    ],
                ),
                dict(
                    label="⏸ Pause", method="animate",
                    args=[[None], {"frame": {"duration": 0, "redraw": False},
                                   "mode": "immediate", "transition": {"duration": 0}}],
                ),
            ],
        )
    ],
)

fig.show(config={"responsive": True})