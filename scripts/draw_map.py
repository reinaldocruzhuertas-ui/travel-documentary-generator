import plotly.graph_objects as go

latitudes = [
    -33.8698439,  # Sydney
    -35.2975906,  # Canberra
    -37.8142454   # Melbourne
]

longitudes = [
    151.2082848,
    149.1012676,
    144.9631732
]

cities = [
    "Sydney",
    "Canberra",
    "Melbourne"
]

fig = go.Figure()

fig.add_trace(
    go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode="lines+markers+text",
        text=cities,
        textposition="top center",
        line=dict(width=3),
        marker=dict(size=10)
    )
)

fig.update_layout(
    title="Sydney → Canberra → Melbourne",
    geo=dict(
        scope="world",
        projection_type="natural earth",
        showland=True
    )
)

fig.show()