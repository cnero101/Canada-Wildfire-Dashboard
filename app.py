import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import pandas as pd
import plotly.express as px
import tempfile
import os

st.set_page_config(layout="wide", page_title="🔥 Canada Wildfire Dashboard")

@st.cache_data
def load_data():
    gdf = gpd.read_file("firms_canada_latest.geojson")
    gdf["acq_date"] = pd.to_datetime(gdf["acq_date"])
    return gdf

gdf = load_data()

# Sidebar filters
st.sidebar.header("📍 Filters")
provinces = sorted(gdf["province"].dropna().unique().tolist())
selected_province = st.sidebar.selectbox("Select Province", ["All"] + provinces)

if selected_province != "All":
    filtered = gdf[gdf["province"] == selected_province]
else:
    filtered = gdf.copy()

cities = sorted(filtered["city"].dropna().unique().tolist())
selected_city = st.sidebar.selectbox("Select City", ["All"] + cities)

if selected_city != "All":
    filtered = filtered[filtered["city"] == selected_city]

selected_date = st.sidebar.date_input("Select Date", value=pd.Timestamp.now().date())
filtered = filtered[filtered["acq_date"].dt.date == selected_date]

# Layers
st.sidebar.markdown("### 🧭 Layers")
basemap = st.sidebar.selectbox("Basemap", ["OpenStreetMap", "CartoDB.DarkMatter", "Stamen.Toner"])
show_temp = st.sidebar.checkbox("🌡️ Temperature")
show_wind = st.sidebar.checkbox("💨 Wind")
show_precip = st.sidebar.checkbox("🌧️ Precipitation")
show_landcover = st.sidebar.checkbox("🗺️ Landcover")

# Main layout
st.title("🔥 Canada Wildfire Dashboard")
st.caption("Real-time hotspot monitoring with overlays and insights")

# 🔝 Top: Map + Pie Chart + Metrics
map_col, right_col = st.columns([2.5, 1.5])

with map_col:
    m = leafmap.Map(center=[56, -106], zoom=4, basemap=basemap)
    if not filtered.empty:
        m.add_heatmap(data=filtered, latitude="latitude", longitude="longitude", name="🔥 Heatmap")
        for _, row in filtered.iterrows():
            m.add_marker([row.geometry.y, row.geometry.x],
                         popup=f"🔥 {row['acq_date'].date()}<br>Bright: {row['bright_ti4']}<br>{row['province']} - {row['city']}")
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
        pie_data = filtered["province"].value_counts().reset_index()
        pie_data.columns = ["Province", "Hotspot Count"]
        fig = px.pie(pie_data, names="Province", values="Hotspot Count",
                     title="🔥 Fire Distribution by Province", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🎯 Key Metrics")
    st.metric("🔥 Total Fires", len(filtered))
    if not filtered.empty:
        st.metric("🌡 Max Brightness", f"{filtered['bright_ti4'].max():.1f} K")
        st.metric("📍 Latest City", filtered.iloc[-1]["city"])

# Export section
if not filtered.empty:
    st.markdown("### 💾 Export Filtered Data")
    st.download_button("⬇️ Download CSV", data=filtered.drop(columns="geometry").to_csv(index=False), file_name="filtered_fires.csv")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmp:
        filtered.to_file(tmp.name, driver="GeoJSON")
        tmp.flush()
        with open(tmp.name, "r") as f:
            geojson_str = f.read()
        os.unlink(tmp.name)

    st.download_button("⬇️ Download GeoJSON", data=geojson_str, file_name="filtered_fires.geojson", mime="application/geo+json")

# 🔻 Bottom: Bar chart and line chart
if not filtered.empty:
    st.markdown("### 📍 Top Burning Provinces")
    top_provs = gdf.groupby("province").size().sort_values(ascending=False).head(10)
    fig_bar = px.bar(x=top_provs.index, y=top_provs.values, title="Top Provinces by Hotspots", labels={"x": "Province", "y": "Count"})
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### 📈 Hotspot Trend Over Time")
    trend = gdf.groupby(gdf["acq_date"].dt.date).size()
    st.line_chart(trend)
else:
    st.info("No data available to generate charts.")
