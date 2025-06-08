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
    api_key = "0c4b25f5d51a58283ea27f36666b6d57"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{api_key}/VIIRS_SNPP_C2/CAN/1"
    df = pd.read_csv(url)

    st.write("Available columns in FIRMS data:", df.columns.tolist())

    if "acq_date" in df.columns:
        df["acq_date"] = pd.to_datetime(df["acq_date"])
    elif "date" in df.columns:
        df["acq_date"] = pd.to_datetime(df["date"])
    else:
        st.error("❌ No valid date column found in FIRMS API response.")
        st.stop()

    df["geometry"] = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf["value"] = gdf["bright_ti4"]
    return gdf

gdf = load_firms_data()

# The rest of your dashboard logic follows...
