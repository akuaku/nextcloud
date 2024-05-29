import streamlit as st
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
import pandas as pd
import re

# STEP 1: Load the data
file_path = 'meshblocks-auckland-1.csv'
columns_to_import = ['SA22023_V1_00_NAME_ASCII']
mesh_blocks = pd.read_csv(file_path, usecols=columns_to_import)

# Load the geographical boundaries
sa2_boundaries_file_path = 'sa2_boundaries.csv'
sa2_boundaries = pd.read_csv(sa2_boundaries_file_path)

# STEP 2: Convert all the mesh block data points to WGS84 (latitude/longitude) for plotting on map
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

# Apply coordinate conversion to the SA2 boundaries
sa2_boundaries['coordinates'] = convert_epsg_to_stdlonlat(sa2_boundaries['WKT'].astype(str).tolist())

# Merge mesh_blocks with sa2_boundaries on SA2 code
merged_data = pd.merge(mesh_blocks, sa2_boundaries, left_on='SA22023_V1_00_NAME_ASCII', right_on='SA22023_V1_00_NAME_ASCII')

# STEP 3: Create Tooltip and Popup content from SA22023_V1_00_NAME_ASCII
tooltips = merged_data['SA22023_V1_00_NAME_ASCII'].astype(str).tolist()
coordinates = merged_data['coordinates'].tolist()

# CREATE MAP IN STREAMLIT

# Set up the Streamlit app
st.title("Auckland City Crash Map")

# Create a folium map centered around Auckland, New Zealand
m = folium.Map(location=[-36.8485, 174.7633], zoom_start=12, width='100%', height='80%')

# Add mesh block tile layer to the map
folium.TileLayer('openstreetmap').add_to(m)

# Add polygons representing mesh blocks to the map
for i in range(len(coordinates)):
    poly = coordinates[i]
    tooltip = tooltips[i]
    popup = folium.Popup(tooltip, parse_html=True)
    folium.Polygon(
        locations=poly, 
        color='SteelBlue', 
        weight=1.5, 
        fill=True, 
        fill_color='blue', 
        fill_opacity=0.1, 
        tooltip=tooltip, 
        popup=popup
    ).add_to(m)

# Add layer controls
folium.LayerControl().add_to(m)

# Display the map with the polygon in the Streamlit app
folium_static(m)
