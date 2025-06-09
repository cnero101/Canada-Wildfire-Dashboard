import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide", page_title="🔥 Canada Wildfire Dashboard")

@st.cache_data(ttl=1800)
def load_firms_data():
    token = "4d36c3b504efa11b5b7cb8fc20c392c6"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{{token}}/VIIRS_SNPP_NRT/CAN/1"
    df = pd.read_csv(url)

    st.write("✅ Available columns in FIRMS data:", df.columns.tolist())

    if "acq_date" in df.columns:
        df["acq_date"] = pd.to_datetime(df["acq_date"])
    elif "date" in df.columns:
        df["acq_date"] = pd.to_datetime(df["date"])
    else:
        st.error("❌ No valid date column found in FIRMS API response.")
        st.stop()

    df["geometry"] = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    df["latitude"] = df["geometry"].y
    df["longitude"] = df["geometry"].x
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["value"] = gdf["bright_ti4"] if "bright_ti4" in gdf.columns else 1
    return gdf

# Load data
gdf = load_firms_data()
filtered = gdf.copy()

# Sidebar Filters
st.sidebar.header("📍 Filters")
if "province" in gdf.columns:
    provinces = ["All"] + sorted(gdf["province"].dropna().unique())
    selected_province = st.sidebar.selectbox("Province", provinces)
    if selected_province != "All":
        filtered = filtered[filtered["province"] == selected_province]

if "city" in filtered.columns:
    cities = ["All"] + sorted(filtered["city"].dropna().unique())
    selected_city = st.sidebar.selectbox("City", cities)
    if selected_city != "All":
        filtered = filtered[filtered["city"] == selected_city]

today = pd.Timestamp.now().date()
selected_date = st.sidebar.date_input("Select Date", value=today)
filtered = filtered[filtered["acq_date"].dt.date == selected_date]

# MAIN layout
st.title("🔥 Canada Wildfire Dashboard")
st.caption("Real-time VIIRS fire data via NASA FIRMS API")

# Map + KPIs/Pie side by side
map_col, stats_col = st.columns([3, 1])
with map_col:
    m = leafmap.Map(center=[56, -106], zoom=4, height=500)
    if not filtered.empty:
        m.add_heatmap(data=filtered, latitude="latitude", longitude="longitude", value="value", name="🔥 Heatmap")
        for _, row in filtered.iterrows():
            popup = f"🔥 {row['acq_date'].date()}<br>Bright: {row['bright_ti4']}<br>Conf: {row['confidence']}"
            m.add_marker([row["latitude"], row["longitude"]], popup=popup)
    m.to_streamlit()

with stats_col:
    st.markdown("### 🎯 Key Metrics")
    st.metric("Total Fires", len(filtered))
    if not filtered.empty:
        st.metric("Max Brightness", f"{filtered['bright_ti4'].max():.1f} K")
        st.metric("Latest Detection", str(filtered["acq_date"].max().date()))

    if "province" in filtered.columns:
        pie_data = filtered["province"].value_counts().reset_index()
        pie_data.columns = ["Province", "Fires"]
        fig = px.pie(pie_data, names="Province", values="Fires", title="🔥 Fires by Province", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# Charts Section
st.markdown("### 📈 Trends Over Time")
if not filtered.empty:
    trend = filtered.groupby(filtered["acq_date"].dt.hour).size()
    st.line_chart(trend)

# Export
st.markdown("### 💾 Export Filtered Data")
if not filtered.empty:
    st.download_button("⬇️ Download CSV", data=filtered.to_csv(index=False), file_name="fires_filtered.csv")

else:
    st.warning("No fire data available for the selected filters.")
