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

gdf = load_firms_data()
filtered = gdf.copy()

# UI
st.title("🔥 Canada Wildfire Dashboard")
st.caption("Real-time VIIRS fire data via NASA FIRMS API")

with st.sidebar:
    st.header("📍 Filters")

    # Optional province filter
    if "province" in gdf.columns:
        provinces = ["All"] + sorted(gdf["province"].dropna().unique())
        selected_province = st.selectbox("Select Province", provinces)
        if selected_province != "All":
            filtered = filtered[filtered["province"] == selected_province]

    # Optional city filter
    if "city" in filtered.columns:
        cities = ["All"] + sorted(filtered["city"].dropna().unique())
        selected_city = st.selectbox("Select City", cities)
        if selected_city != "All":
            filtered = filtered[filtered["city"] == selected_city]

    # Date filter
    today = pd.Timestamp.now().date()
    selected_date = st.date_input("Select Date", value=today)
    filtered = filtered[filtered["acq_date"].dt.date == selected_date]

# Show metrics
st.markdown("### 🔥 Fire Detections")
if not filtered.empty:
    st.map(filtered, latitude="latitude", longitude="longitude")
    st.dataframe(filtered[["acq_date", "latitude", "longitude", "confidence", "bright_ti4"]].head())
    st.metric("Total Fires", len(filtered))
    st.metric("Max Brightness", f"{filtered['bright_ti4'].max():.1f} K")
else:
    st.warning("No fire data for the selected filters.")
