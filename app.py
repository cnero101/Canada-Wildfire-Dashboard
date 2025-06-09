import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide", page_title="🔥 Canada Wildfire Dashboard")

@st.cache_data
def load_local_data():
    df = pd.read_csv("MODIS_C6_Canada_7d.csv")
    df["acq_date"] = pd.to_datetime(df["acq_date"], errors="coerce")
    df = df.dropna(subset=["acq_date", "latitude", "longitude"])
    df["geometry"] = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["value"] = gdf["brightness"] if "brightness" in gdf.columns else 1
    return gdf

gdf = load_local_data()

# Sidebar filters
st.sidebar.header("📍 Filters")
available_dates = gdf["acq_date"].dt.date.unique()
selected_date = st.sidebar.date_input("Select Date", value=max(available_dates), min_value=min(available_dates), max_value=max(available_dates))
filtered = gdf[gdf["acq_date"].dt.date == selected_date]

# Main layout
st.markdown("## 🔥 Canada Wildfire Dashboard")
st.caption("Real-time hotspot monitoring with climate overlays and dynamic indicators")

map_col, metrics_col = st.columns([3, 1])

with map_col:
    m = leafmap.Map(center=[56, -106], zoom=4, height=480)
    if not filtered.empty:
        m.add_heatmap(data=filtered, latitude="latitude", longitude="longitude", value="value", name="🔥 Heatmap")
        for _, row in filtered.iterrows():
            popup = f"🔥 {row['acq_date'].date()}<br>Bright: {row['brightness']}<br>Conf: {row['confidence']}"
            m.add_marker([row["latitude"], row["longitude"]], popup=popup)
    m.to_streamlit()

with metrics_col:
    st.markdown("### 🎯 Key Metrics")
    st.metric("Total Fires", len(filtered))
    if not filtered.empty:
        st.metric("Max Brightness", f"{filtered['brightness'].max():.1f}")
        st.metric("Latest Detection", str(filtered["acq_date"].max().date()))
        st.metric("Latest City", "Red Deer")  # Placeholder or dynamically extract city later

    st.markdown("### 📊 Visual Insights")
    if not filtered.empty:
        fig = px.pie(filtered, names="satellite", title="🔥 Fires by Satellite", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# Charts below map
st.markdown("### 📈 Trends Over Time")
chart_col1, chart_col2 = st.columns(2)

if not filtered.empty:
    with chart_col1:
        time_group = filtered.groupby(filtered["acq_date"].dt.hour).size()
        fig = px.bar(x=time_group.index, y=time_group.values, labels={"x": "Hour", "y": "Fire Count"}, title="Hourly Fire Count")
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        trend = filtered.groupby(filtered["acq_date"].dt.hour)["brightness"].mean()
        fig = px.line(x=trend.index, y=trend.values, labels={"x": "Hour", "y": "Avg Brightness"}, title="Brightness Trend")
        st.plotly_chart(fig, use_container_width=True)

# Export
st.markdown("### 💾 Export Filtered Data")
if not filtered.empty:
    st.download_button("⬇️ Download CSV", data=filtered.to_csv(index=False), file_name="fires_filtered.csv")
else:
    st.warning("No fire data for selected date.")
