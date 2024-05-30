import streamlit as st
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
import pandas as pd
import re

# Load the crash data with date and crashes count
file_path = 'output_crash.csv'
columns_to_import = ['WKT', 'SA22023_V1_00_NAME_ASCII_y', 'crashesCount', 'date']
crash_data = pd.read_csv(file_path, usecols=columns_to_import)

# Explicitly specify the date format
crash_data['date'] = pd.to_datetime(crash_data['date'], format='%d/%m/%Y', errors='coerce')

# Check for any parsing errors
if crash_data['date'].isnull().any():
    st.warning("Some dates could not be parsed. Please check the format in the CSV file.")

# Date selection
st.title("Auckland City Crash Map")
selected_date = st.date_input("Select a date", crash_data['date'].min())

# Filter the crash data based on the selected date
filtered_crash_data = crash_data[crash_data['date'] == pd.to_datetime(selected_date)]

# Convert "WKT" to list with a polygon string for each row
coordinates = filtered_crash_data['WKT'].astype(str).tolist()

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

# Create Tooltip and Popup content from SA22022_V1_00_NAME_ASCII and crashes count
tooltips = []
for i, row in filtered_crash_data.iterrows():
    tooltip = f"{row['SA22023_V1_00_NAME_ASCII_y']}<br>Crashes Count: {row['crashesCount']}"
    tooltips.append(tooltip)

# CREATE MAP IN STREAMLIT

# Create a folium map centered around Auckland, New Zealand
m = folium.Map(location=[-36.8485, 174.7633], zoom_start=12)

# Add mesh block tile layer to the map
folium.TileLayer('openstreetmap').add_to(m)

# Add polygons representing mesh blocks to the map
for i in range(len(polygon_coords_list)):
    poly = polygon_coords_list[i]
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
