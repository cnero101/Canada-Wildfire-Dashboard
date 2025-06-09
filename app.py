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
    gdf["value"] = gdf["brightness"]
    return gdf

gdf = load_local_data()

# Sidebar Filters
st.sidebar.header("📍 Filters")
province = st.sidebar.selectbox("Select Province", options=["All", "Quebec", "Alberta", "Ontario"], index=0)
city = st.sidebar.selectbox("Select City", options=["All", "Red Deer", "Toronto"], index=0)
available_dates = gdf["acq_date"].dt.date.unique()
selected_date = st.sidebar.date_input("Select Date", value=max(available_dates))

st.sidebar.markdown("### 🗺️ Basemap")
basemap = st.sidebar.selectbox("Basemap", options=["OpenStreetMap", "CartoDB.Positron", "CartoDB.DarkMatter"])

st.sidebar.markdown("### 🌐 Layers")
show_hotspots = st.sidebar.checkbox("🔥 Hotspots", value=True)
show_temp = st.sidebar.checkbox("🌡️ Temperature")
show_wind = st.sidebar.checkbox("💨 Wind")
show_precip = st.sidebar.checkbox("🌧️ Precipitation")

# Filter logic
filtered = gdf[gdf["acq_date"].dt.date == selected_date]

# Top Layout: Map + KPIs + Pie
st.markdown("## 🔥 Canada Wildfire Dashboard")
st.caption("Real-time hotspot monitoring with overlays and insights")

map_col, stats_col = st.columns([3, 1], gap="large")

with map_col:
    m = leafmap.Map(center=[56, -106], zoom=4, height=500, basemap=basemap)
    if not filtered.empty:
        if show_hotspots:
            m.add_heatmap(data=filtered, latitude="latitude", longitude="longitude", value="value", name="🔥 Heatmap")
        for _, row in filtered.iterrows():
            popup = f"🔥 {row['acq_date'].date()}<br>Bright: {row['brightness']}<br>Conf: {row['confidence']}"
            m.add_marker([row["latitude"], row["longitude"]], popup=popup)
    m.to_streamlit()

with stats_col:
    st.markdown("### 🎯 Key Metrics")
    st.metric("Total Fires", len(filtered))
    if not filtered.empty:
        st.metric("Max Brightness", f"{filtered['brightness'].max():.1f}")
        st.metric("Latest Detection", str(filtered["acq_date"].max().date()))
        st.metric("Latest City", "Red Deer")

    st.markdown("### 🔥 Fire Distribution")
    if not filtered.empty:
        fire_by_sat = filtered["satellite"].value_counts(normalize=True) * 100
        fig = px.pie(names=fire_by_sat.index, values=fire_by_sat.values, title="Fire % by Satellite", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# Below Map: Dual Chart Section
st.markdown("### 📊 Trends and Distribution")

chart_col1, chart_col2 = st.columns(2)
if not filtered.empty:
    with chart_col1:
        trend = filtered.groupby(filtered["acq_date"].dt.hour).size()
        fig = px.bar(x=trend.index, y=trend.values, labels={"x": "Hour", "y": "Fire Count"}, title="Hourly Fire Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        avg_brightness = filtered.groupby(filtered["acq_date"].dt.hour)["brightness"].mean()
        fig = px.line(x=avg_brightness.index, y=avg_brightness.values, labels={"x": "Hour", "y": "Avg Brightness"}, title="Brightness Trend")
        st.plotly_chart(fig, use_container_width=True)

# Export
st.markdown("### 💾 Export Filtered Data")
if not filtered.empty:
    st.download_button("⬇️ Download CSV", data=filtered.to_csv(index=False), file_name="filtered_fires.csv")
else:
    st.warning("No fire data available for selected date.")
