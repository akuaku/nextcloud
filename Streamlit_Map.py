
# Maps on Streamlit
import streamlit as st
import folium
from streamlit_folium import folium_static
from pyproj import Transformer

# Data manipulation
import pandas as pd
import numpy as np
import re

# DATA PROCESSING

# STEP1 : Convert all the mesh block data points to WGS84 (latitude/longitude) for plotting on map
# Read in file
file_path = 'meshblocks-auckland.csv'
columns_to_import = ['WKT', 'SA22022_V1_00_NAME_ASCII']
mesh_blocks = pd.read_csv(file_path, usecols=columns_to_import)

# Convert "WKT" to list with a polygon string for each row
coordinates = row_strings = mesh_blocks['WKT'].astype(str).tolist()

# Converts str list format to standard lon, lat coordinates.
# New Zealand Transverse Mercator 2000 to EPSG:4326 WGS 84
def convert_epsg_to_stdlonlat(coordinates_list):
    polygon_coords_list = []

    def convert_long_lat_pairs(coords):
        # Find all numeric values in the string
        numeric_values = re.findall(r'-?\d+\.\d+', coords)

        # Convert numeric values to pairs of longitude and latitude enclosed in square brackets
        pairs = [[float(numeric_values[i]), float(numeric_values[i+1])] for i in range(0, len(numeric_values), 2)]
        
        return pairs

    # Define the EPSG codes
    input_epsg = 'EPSG:2193'  # New Zealand Transverse Mercator 2000
    output_epsg = 'EPSG:4326'  # WGS84 (latitude/longitude)

    # Create a PyProj transformer
    transformer = Transformer.from_crs(input_epsg, output_epsg)

    for coords in coordinates_list:
        # Convert coordinates to long/lat pairs
        coordinate_pairs = convert_long_lat_pairs(coords)
        
        # Initialize an empty list to store coordinate pairs
        polygon_coords = []
        
        # Loop through each coordinate pair
        for pair in coordinate_pairs:
            # Convert coordinates from EPSG:2193 to EPSG:4326
            lon, lat = transformer.transform(pair[1], pair[0])
            polygon_coords.append([lon, lat])  # Append the coordinate pair to the list
        
        # Append the list of coordinate pairs for this polygon to the main list
        polygon_coords_list.append(polygon_coords)

    return polygon_coords_list

polygon_coords_list = convert_epsg_to_stdlonlat(coordinates)

# STEP 2: Create Tooltip files from SA22022_V1_00_NAME_ASCII
tooltips = mesh_blocks['SA22022_V1_00_NAME_ASCII'].astype(str).tolist()


# CREATE MAP IN STREAMLIT

# Set up the Streamlit app
st.title("Auckland City Crash Map")

# Create a folium map centered around Auckland, New Zealand
m = folium.Map(location=[-36.8485, 174.7633], zoom_start=12, width=1000, height=800)

# Add mesh block tile layer to the map
folium.TileLayer('openstreetmap').add_to(m)

# Add polygons representing mesh blocks to the map
for i in range(len(polygon_coords_list)):
    poly = polygon_coords_list[i]
    folium.Polygon(locations=poly, color='SteelBlue', weight=1.5, fill=True, fill_color='blue', 
                   fill_opacity=0.1, tooltip=tooltips[i]).add_to(m)

# Add layer controls
folium.LayerControl().add_to(m)

# Display the map with the polygon in the Streamlit app
folium_static(m)



