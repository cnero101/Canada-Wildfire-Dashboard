import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import leafmap.foliumap as leafmap
import tempfile
import os

st.set_page_config(layout="wide", page_title="🔥 Canada Wildfire Dashboard")

@st.cache_data(ttl=1800)
def load_firms_data():
    url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs/csv/VIIRS_Canada_24h.csv"
    df = pd.read_csv(url)
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    df["geometry"] = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["value"] = gdf["bright_ti4"]
    return gdf

gdf = load_firms_data()

# Sidebar filters
st.sidebar.header("📍 Filters")
provinces = sorted(gdf["province"].dropna().unique()) if "province" in gdf.columns else []
selected_province = st.sidebar.selectbox("Select Province", ["All"] + provinces)

if selected_province != "All":
    filtered = gdf[gdf["province"] == selected_province]
else:
    filtered = gdf.copy()

cities = sorted(filtered["city"].dropna().unique()) if "city" in filtered.columns else []
selected_city = st.sidebar.selectbox("Select City", ["All"] + cities)

if selected_city != "All":
    filtered = filtered[filtered["city"] == selected_city]

selected_date = st.sidebar.date_input("Select Date", value=pd.Timestamp.now().date())
filtered = filtered[filtered["acq_date"].dt.date == selected_date]

# Basemap and overlay toggles
st.sidebar.markdown("### 🧭 Layers")
basemap = st.sidebar.selectbox("Basemap", ["OpenStreetMap", "CartoDB.DarkMatter", "Stamen.Toner"])
show_temp = st.sidebar.checkbox("🌡️ Temperature")
show_wind = st.sidebar.checkbox("💨 Wind")
show_precip = st.sidebar.checkbox("🌧️ Precipitation")
show_landcover = st.sidebar.checkbox("🗺️ Landcover")

# Main layout
st.title("🔥 Canada Wildfire Dashboard")
st.caption("Real-time FIRMS VIIRS 24h data feed from NASA")

# Top: Map + Pie + KPIs
map_col, right_col = st.columns([2.5, 1.5])
with map_col:
    m = leafmap.Map(center=[56, -106], zoom=4, basemap=basemap)
    if not filtered.empty:
        m.add_heatmap(data=filtered, latitude="latitude", longitude="longitude", value="value", name="🔥 Heatmap")
        for _, row in filtered.iterrows():
            popup = f"🔥 {row['acq_date'].date()}<br>Bright: {row['bright_ti4']}<br>Conf: {row['confidence']}"
            m.add_marker([row["latitude"], row["longitude"]], popup=popup)
    if show_temp:
        m.add_tile_layer("https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=demo", "Temperature", "OpenWeatherMap")
    if show_wind:
        m.add_tile_layer("https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=demo", "Wind", "OpenWeatherMap")
    if show_precip:
        m.add_tile_layer("https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=demo", "Precipitation", "OpenWeatherMap")
    if show_landcover:
        m.add_tile_layer("https://tiles.arcgis.com/tiles/P3ePLMYs2RVChkJx/arcgis/rest/services/ESA_WorldCover_10m_2021/ImageServer/tile/{z}/{y}/{x}", "Landcover", "ESA")
    m.add_layer_control()
    m.to_streamlit(height=520)

with right_col:
    if not filtered.empty:
        fig = px.pie(
            filtered,
            names="confidence",
            title="🔥 Confidence Distribution",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🎯 Key Metrics")
    st.metric("🔥 Total Fires", len(filtered))
    if not filtered.empty:
        st.metric("🌡 Max Brightness", f"{filtered['bright_ti4'].max():.1f} K")

# Export and Trends
if not filtered.empty:
    st.markdown("### 💾 Export Filtered Data")
    st.download_button("⬇️ Download CSV", data=filtered.to_csv(index=False), file_name="firms_filtered.csv")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmp:
        filtered[["latitude", "longitude", "acq_date", "bright_ti4", "confidence"]].to_csv(tmp.name, index=False)
        tmp.flush()
        with open(tmp.name, "r") as f:
            geojson_str = f.read()
        os.unlink(tmp.name)
    st.download_button("⬇️ Download Table CSV", data=geojson_str, file_name="filtered_table.csv")

    st.markdown("### 📈 Fire Trends")
    trend = filtered.groupby(filtered["acq_date"].dt.hour).size()
    st.line_chart(trend)

else:
    st.warning("No FIRMS fire data available for selected filters.")
