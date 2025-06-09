import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide", page_title="🔥 Canada Wildfire Dashboard (Demo)")

@st.cache_data
def load_demo_data():
    url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/MODIS_C6_Canada_7d.csv"
    df = pd.read_csv(url)

    if "acq_date" in df.columns:
        df["acq_date"] = pd.to_datetime(df["acq_date"])
    else:
        st.error("❌ acq_date column missing in static file.")
        st.stop()

    df["geometry"] = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    df["latitude"] = df["geometry"].y
    df["longitude"] = df["geometry"].x
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["value"] = gdf["brightness"]
    return gdf

gdf = load_demo_data()
filtered = gdf.copy()

# Sidebar filters
st.sidebar.header("📍 Filters")
today = pd.Timestamp.now().date()
selected_date = st.sidebar.date_input("Select Date", value=today)
filtered = filtered[filtered["acq_date"].dt.date == selected_date]

# Main layout
st.title("🔥 Canada Wildfire Dashboard (Static Demo)")
st.caption("MODIS C6 - last 7 days (public feed)")

map_col, stats_col = st.columns([3, 1])
with map_col:
    m = leafmap.Map(center=[56, -106], zoom=4, height=500)
    if not filtered.empty:
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

# Pie chart
if not filtered.empty:
    fig = px.pie(filtered, names="satellite", title="🔥 Fires by Satellite", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# Trend
st.markdown("### 📈 Hourly Trend")
if not filtered.empty:
    trend = filtered.groupby(filtered["acq_date"].dt.hour).size()
    st.line_chart(trend)

# Export
st.markdown("### 💾 Export Filtered Data")
if not filtered.empty:
    st.download_button("⬇️ Download CSV", data=filtered.to_csv(index=False), file_name="fires_demo_filtered.csv")
else:
    st.warning("No fire data for the selected date.")
