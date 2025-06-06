import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import pandas as pd

st.set_page_config(layout="wide", page_title="🔥 Canada Wildfire Dashboard")

@st.cache_data
def load_data():
    gdf = gpd.read_file("firms_canada_latest.geojson")
    gdf["acq_date"] = pd.to_datetime(gdf["acq_date"])
    return gdf

gdf = load_data()

# --- Dynamic dropdowns ---
provinces = sorted(gdf["province"].dropna().unique().tolist())
selected_province = st.sidebar.selectbox("Select Province", ["All"] + provinces)

if selected_province != "All":
    filtered_gdf = gdf[gdf["province"] == selected_province]
else:
    filtered_gdf = gdf.copy()

cities = sorted(filtered_gdf["city"].dropna().unique().tolist())
selected_city = st.sidebar.selectbox("Select City", ["All"] + cities)

if selected_city != "All":
    filtered_gdf = filtered_gdf[filtered_gdf["city"] == selected_city]

selected_date = st.sidebar.date_input("Select Date", value=pd.Timestamp.now().date())
filtered_gdf = filtered_gdf[filtered_gdf["acq_date"].dt.date == selected_date]

# --- Basemap and overlays ---
basemap = st.sidebar.selectbox("Basemap", ["OpenStreetMap", "CartoDB.DarkMatter", "Stamen.Toner"])
show_temp = st.sidebar.checkbox("🌡️ Temperature")
show_wind = st.sidebar.checkbox("🌬️ Wind")
show_precip = st.sidebar.checkbox("🌧️ Precipitation")
show_landcover = st.sidebar.checkbox("🌍 Landcover")

# --- Main Layout ---
st.title("🔥 Canada Wildfire Dashboard")
st.caption("Filtered NASA FIRMS hotspots with dynamic overlays")

col1, col2 = st.columns([2, 1])

with col1:
    m = leafmap.Map(center=[56, -106], zoom=4, basemap=basemap)
    if not filtered_gdf.empty:
        filtered_gdf["popup"] = (
            "🔥 Date: " + filtered_gdf["acq_date"].astype(str) +
            "<br>Brightness: " + filtered_gdf["bright_ti4"].astype(str) +
            "<br>Confidence: " + filtered_gdf["confidence"] +
            "<br>City: " + filtered_gdf["city"]
        )
        m.add_gdf(filtered_gdf, layer_name="Hotspots", info_mode="on_hover", popup=filtered_gdf["popup"])

    if show_temp:
        m.add_tile_layer(
            url="https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=demo",
            name="Temperature", attribution="OpenWeatherMap"
        )
    if show_wind:
        m.add_tile_layer(
            url="https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=demo",
            name="Wind", attribution="OpenWeatherMap"
        )
    if show_precip:
        m.add_tile_layer(
            url="https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=demo",
            name="Precipitation", attribution="OpenWeatherMap"
        )
    if show_landcover:
        m.add_tile_layer(
            url="https://tiles.arcgis.com/tiles/P3ePLMYs2RVChkJx/arcgis/rest/services/ESA_WorldCover_10m_2021/ImageServer/tile/{z}/{y}/{x}",
            name="Landcover", attribution="ESA WorldCover"
        )

    m.add_layer_control()
    m.to_streamlit(height=550)

with col2:
    st.markdown("### 🔢 Key Metrics")
    st.metric("🔥 Total Fires", len(filtered_gdf))
    if not filtered_gdf.empty:
        st.metric("🌡 Max Brightness", f"{filtered_gdf['bright_ti4'].max():.1f} K")
        st.metric("📍 Latest City", filtered_gdf.iloc[-1]["city"])
    else:
        st.write("No data for selected filters.")

# --- Charts Below ---
st.markdown("### 📊 Confidence Breakdown")
if not filtered_gdf.empty:
    conf_counts = filtered_gdf["confidence"].value_counts()
    st.plotly_chart(conf_counts.plot.pie(autopct='%1.1f%%', title="Confidence Levels").figure, use_container_width=True)

st.markdown("### 📈 Trends Over Time")
if not filtered_gdf.empty:
    daily_counts = gdf.groupby(gdf["acq_date"].dt.date).size()
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.bar_chart(daily_counts)
    with chart_col2:
        st.line_chart(daily_counts.rolling(2).mean())
else:
    st.warning("No data to plot trend charts.")
