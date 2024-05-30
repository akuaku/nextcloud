import streamlit as st
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
import pandas as pd
import re
from datetime import datetime

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

file_path = 'output_crash.csv'
data = load_data(file_path)

# Convert date column to datetime format with dayfirst=True
data['date'] = pd.to_datetime(data['date'], dayfirst=True)

# Create a sidebar for filters
st.sidebar.header("Filters")

# Create date, part of day, and crash area input widgets
selected_date = st.sidebar.date_input("Select a date", value=datetime.today())
selected_part_of_day = st.sidebar.selectbox("Select part of day", options=['day', 'night'])
selected_crash_area = st.sidebar.selectbox("Select crash area type", options=['all','low crash area', 'high crash area' ])

# Filter the data based on the selected date and part of day
filtered_data = data[(data['date'].dt.date == selected_date) & (data['partOfDay'] == selected_part_of_day)]

# Further filter the data based on the selected crash area type
if selected_crash_area == 'low crash area':
    filtered_data = filtered_data[filtered_data['crashesCount'] == 0]
elif selected_crash_area == 'high crash area':
    filtered_data = filtered_data[filtered_data['crashesCount'] == 1]

# Check if there is data for the selected filters
if filtered_data.empty:
    st.warning("No data available for the selected filters.")
else:
    # Convert "WKT" to list with a polygon string for each row
    coordinates = filtered_data['WKT'].astype(str).tolist()

    # Convert str list format to standard lon, lat coordinates.
    def convert_epsg_to_stdlonlat(coordinates_list):
        polygon_coords_list = []

        def convert_long_lat_pairs(coords):
            numeric_values = re.findall(r'-?\d+\.\d+', coords)
            pairs = [[float(numeric_values[i]), float(numeric_values[i+1])] for i in range(0, len(numeric_values), 2)]
            return pairs

        input_epsg = 'EPSG:2193'
        output_epsg = 'EPSG:4326'
        transformer = Transformer.from_crs(input_epsg, output_epsg)

        for coords in coordinates_list:
            coordinate_pairs = convert_long_lat_pairs(coords)
            polygon_coords = []

            for pair in coordinate_pairs:
                lon, lat = transformer.transform(pair[1], pair[0])
                polygon_coords.append([lon, lat])

            polygon_coords_list.append(polygon_coords)

        return polygon_coords_list

    polygon_coords_list = convert_epsg_to_stdlonlat(coordinates)

    crashes_counts = filtered_data['crashesCount'].astype(str).tolist()
    tooltips = filtered_data['SA22023_V1_00_NAME_ASCII_y'].astype(str).tolist()

    # CREATE MAP IN STREAMLIT
    st.title("Auckland City Crash Map")

    # Create a folium map centered around Auckland, New Zealand
    m = folium.Map(location=[-36.8485, 174.7633], zoom_start=14, width='100%', height='80%')

    # Add mesh block tile layer to the map
    folium.TileLayer('openstreetmap').add_to(m)

    # Add polygons representing mesh blocks to the map
    for i in range(len(polygon_coords_list)):
        poly = polygon_coords_list[i]
        tooltip = tooltips[i]
        crashes_count = crashes_counts[i]
        
        if crashes_count == "0":
            crash_info = "There will be 3 or less crashes"
        else:
            crash_info = "There will be 4 or more crashes"
        
        popup_content = f"{crash_info}"
        popup = folium.Popup(popup_content, parse_html=True)
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
