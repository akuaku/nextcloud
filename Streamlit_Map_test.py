import streamlit as st
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
import pandas as pd
import re
from datetime import datetime

# Set the layout to wide mode
st.set_page_config(layout="wide")

@st.cache_data
def load_data(file_path):
    return pd.read_parquet(file_path)

file_path = 'output_crash.parquet'
data = load_data(file_path)

# Convert date column to datetime format with dayfirst=True
data['date'] = pd.to_datetime(data['date'], dayfirst=True)

# Get the unique dates available in the data
available_dates = data['date'].dt.date.unique()
min_date = min(available_dates)
max_date = max(available_dates)

# Create sidebar for filters
st.sidebar.header("Filters")
selected_date = st.sidebar.date_input("Select a date", value=min_date, min_value=min_date, max_value=max_date)
selected_part_of_day = st.sidebar.selectbox("Select part of day", options=['day', 'night'])
selected_crash_area = st.sidebar.selectbox("Select crash area type", options=['all', 'low crash area', 'high crash area'])

# Filter the data based on the selected date and part of day
filtered_data = data[(data['date'].dt.date == selected_date) & (data['partOfDay'] == selected_part_of_day)]

# Further filter the data based on the selected crash area type
if selected_crash_area == 'low crash area':
    filtered_data = filtered_data[filtered_data['predicted_value'] == 0]
elif selected_crash_area == 'high crash area':
    filtered_data = filtered_data[filtered_data['predicted_value'] == 1]

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
            
            # Ensure that we have an even number of numeric values
            if len(numeric_values) % 2 != 0:
                return []
            
            pairs = [[float(numeric_values[i]), float(numeric_values[i+1])] for i in range(0, len(numeric_values), 2)]
            return pairs

        input_epsg = 'EPSG:2193'
        output_epsg = 'EPSG:4326'
        transformer = Transformer.from_crs(input_epsg, output_epsg)

        for coords in coordinates_list:
            coordinate_pairs = convert_long_lat_pairs(coords)
            
            # Skip invalid coordinate pairs
            if not coordinate_pairs:
                continue
            
            polygon_coords = []
            for pair in coordinate_pairs:
                lon, lat = transformer.transform(pair[1], pair[0])
                polygon_coords.append([lon, lat])
            polygon_coords_list.append(polygon_coords)

        return polygon_coords_list

    polygon_coords_list = convert_epsg_to_stdlonlat(coordinates)

    crashes_counts = filtered_data['predicted_value'].astype(str).tolist()
    tooltips = filtered_data['SA2_Name'].astype(str).tolist()

    # Create the map
    st.title("Auckland Accident Hotspot Model")
    m = folium.Map(location=[-36.8485, 174.7633], zoom_start=13)

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
            color='#ff7f08',
            weight=3,
            fill=True,
            fill_color='#ff7f08',
            fill_opacity=0.3,
            tooltip=tooltip,
            popup=popup
        ).add_to(m)

    # Display the map with the polygon in the Streamlit app
    st.markdown(
        """
        <style>
        .stApp {
            padding: 0;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 {
            margin-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    folium_static(m, width=1100, height=600)
