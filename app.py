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
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{token}/VIIRS_SNPP_NRT/CAN/1"
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
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["value"] = gdf["bright_ti4"] if "bright_ti4" in gdf.columns else 1
    return gdf

gdf = load_firms_data()
st.title("🔥 Canada Wildfire Dashboard")
st.caption("Real-time VIIRS fire data via NASA FIRMS API")

# Simple visual check
if not gdf.empty:
    st.map(gdf, latitude="latitude", longitude="longitude")
    st.dataframe(gdf.head())
else:
    st.warning("No data available.")
