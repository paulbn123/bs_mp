import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np


# Set page config
st.set_page_config(page_title="Portfolio Dashboard", 
                   layout="wide",
                   page_icon="🔓",  # Unlocked padlock emoji
                   initial_sidebar_state="expanded")  # Make sure sidebar is expanded

# Add custom CSS to reduce gap between top of page and title
st.markdown("""
<style>
    .block-container {
        padding-top: 0.5rem !important;
        margin-top: 0.5rem !important;
    }
    .main > div {
        padding-top: 0.5rem !important;
    }
    div[data-testid="stAppViewContainer"] > .main {
        padding-top: 0rem !important;
    }
</style>
""", unsafe_allow_html=True)

# # Hide the main menu (hamburger menu)
# st.markdown("""
# <style>
# #MainMenu {visibility: hidden;}
# </style>
# """, unsafe_allow_html=True)

# # Hide the footer
# st.markdown("""
# <style>
# footer {visibility: hidden;}
# </style>
# """, unsafe_allow_html=True)

# # Hide the header (including GitHub, Share, etc.) - Modified to not affect sidebar
# st.markdown("""
# <style>
# /* Hide header elements but preserve sidebar */
# header[data-testid="stHeader"] {visibility: hidden;}

# /* Ensure sidebar is always visible - multiple selectors for different Streamlit versions */
# .css-1d391kg {visibility: visible !important; display: block !important;}
# section[data-testid="stSidebar"] {visibility: visible !important; display: block !important;}
# .css-1lcbmhc {visibility: visible !important; display: block !important;}
# .css-17eq0hr {visibility: visible !important; display: block !important;}
# div[data-testid="stSidebar"] {visibility: visible !important; display: block !important;}

# /* Force sidebar visibility with higher specificity */
# .stApp > div > div > section[data-testid="stSidebar"] {
#     visibility: visible !important;
#     display: block !important;
#     opacity: 1 !important;
# }

# /* Additional fallback for sidebar visibility */
# [data-testid="stSidebar"] > div {
#     visibility: visible !important;
#     display: block !important;
# }
# </style>
# """, unsafe_allow_html=True)


# Title
st.title("Store Map Dashboard")

# Display columns for data table
DISPLAY_COLUMNS = ['storename', 'value_2024', 'absolute_value_change', 'value_2025']
DISPLAY_COLUMNS_DISPLAY_NAMES = ['Store', '2024 Value', 'Change in value', '2025 Value']
INTEGER_COLUMNS = ['value_2024', 'value_2025', 'absolute_value_change', 'Area']
FLOAT_COLUMNS = ['latitude', 'longitude', 'percentage_value_change']
ENCODINGS_TO_TRY = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16', 'utf-8-sig']


# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False

# File uploader - only show if no data loaded
if not st.session_state.file_uploaded:
    uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
    
    if uploaded_file is not None:
        st.toast(f"File uploaded: {uploaded_file.name}")
        
        # Read the CSV file with multiple encoding attempts
        try:
              
            df = None
            error_messages = []
            
            # Try different encodings in order of likelihood
            for encoding in ENCODINGS_TO_TRY:
                try:
                    # Reset file pointer for each attempt
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    st.success(f"✅ CSV loaded successfully with {encoding} encoding")
                    break
                except UnicodeDecodeError as e:
                    error_messages.append(f"{encoding}: {str(e)[:100]}...")
                    continue
                except Exception as e:
                    error_messages.append(f"{encoding}: {str(e)[:100]}...")
                    continue
            
            if df is None:
                st.error("❌ Could not read the CSV file with any supported encoding")
                with st.expander("🔍 Detailed Error Messages", expanded=False):
                    for msg in error_messages:
                        st.write(f"• {msg}")
                
                st.info("**Troubleshooting steps:**")
                st.write("1. Try opening your CSV in a text editor (like Notepad++) to check the encoding")
                st.write("2. In Excel: Save As → CSV UTF-8 (Comma delimited)")
                st.write("3. Check if there are any special characters in the new city column")
                st.write("4. Try removing the city column temporarily to see if the file loads")
                st.write("5. Check the file size - make sure it's not corrupted")
                
                # Show first few bytes of the file for debugging
                uploaded_file.seek(0)
                first_bytes = uploaded_file.read(50)
                st.write(f"**First 50 bytes of file:** {first_bytes}")
                
                st.stop()
                
            st.toast(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Verify required columns exist (updated to include entity)
            required_columns = ['storename', 'operator_name', 'entity', 'country', 'city', 'latitude', 'longitude', 
                              'value_2024', 'value_2025', 'absolute_value_change', 'percentage_value_change',
                              'Tenure', 'Area']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
                st.error("Please ensure your CSV contains all required columns.")
                st.stop()
            else:
                st.toast("✅ All required columns found!")
            
            # Convert data types properly
            try:
                # Convert integer columns
                for col in INTEGER_COLUMNS:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        # Fill NaN with 0 and convert to regular int to avoid Arrow issues
                        df[col] = df[col].fillna(0).astype('int64')
                
                # Convert float columns
                for col in FLOAT_COLUMNS:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Ensure string columns are properly typed (updated to include entity)
                string_columns = ['storename', 'operator_name', 'entity', 'country', 'city', 'Tenure']
                for col in string_columns:
                    if col in df.columns:
                        df[col] = df[col].astype(str).replace('nan', '')  # Convert NaN to empty string
                
                st.success("✅ Data types converted successfully")
                
                # Store in session state
                st.session_state.df = df
                st.session_state.file_uploaded = True
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error converting data types: {str(e)}")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.error("**Common issues:**")
            st.write("- Check if the file is a valid CSV format")
            st.write("- Ensure column names match exactly (case-sensitive)")
            st.write("- Check for special characters in the file")
            st.write("- Verify the file is not corrupted")
            st.info("Please ensure your CSV file contains the required columns: storename, operator_name, entity, country, city, latitude, longitude, value_2024, value_2025, absolute_value_change, percentage_value_change, Tenure, Area")

# Only proceed if data is loaded
if st.session_state.file_uploaded and st.session_state.df is not None:
    df = st.session_state.df
    
    # Clean data - remove rows with missing lat/lon
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Sidebar filters and data info
    st.sidebar.header("Filters")
    
    # Data Upload & Quality Information in sidebar expander (when file is uploaded)
    with st.sidebar.expander("📁 Data Upload & Quality Information", expanded=False):

        # Reset data button
        if st.button("🔄 Upload New File"):
            st.session_state.df = None
            st.session_state.file_uploaded = False
            st.rerun()

        st.info(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Data preview
        st.subheader("Data Preview")
        st.dataframe(df.head(), use_container_width=True)
        
        # Data quality check
        st.subheader("Data Quality Check")
        missing_coords = df[['latitude', 'longitude']].isnull().any(axis=1).sum()
        if missing_coords > 0:
            st.warning(f"⚠️ {missing_coords} rows have missing latitude/longitude and will be excluded")
        else:
            st.success("✅ All location data is valid")
        
        # Show data types
        st.subheader("Data Types")
        st.write(df.dtypes)

    # Store filters in sidebar expander
    with st.sidebar.expander("🏪 Store Filters", expanded=False):  

        # Operator filter (before entity filter)
        st.subheader("Operator")
        operators = ['All'] + sorted(df['operator_name'].unique().tolist())
        selected_operator = st.radio("Select Operator:", operators, key="operator_radio")

        # Entity filter - depends on operator selection
        st.subheader("Entity")
        
        # Filter entities based on operator selection
        if selected_operator != 'All':
            entity_filter_df = df[df['operator_name'] == selected_operator]
        else:
            entity_filter_df = df.copy()
        
        available_entities = entity_filter_df['entity'].unique().tolist()
        entities = ['All'] + sorted(available_entities)
        selected_entity = st.radio("Select Entity:", entities, key="entity_radio")

        # Tenure filter
        st.subheader("Tenure")
        tenures = ['All'] + sorted(df['Tenure'].unique().tolist())
        selected_tenure = st.radio("Select Tenure:", tenures, key="tenure_radio")
    
        # Area filter
        st.subheader("Area")
        area_clean = df['Area'].dropna()
        if len(area_clean) > 0:
            area_min, area_max = int(area_clean.min()), int(area_clean.max())
            if area_min == area_max:
                area_range = (area_min, area_max)
                st.write(f"All stores have the same area: {area_min:,}")
            else:
                area_range = st.slider(
                    "Select Area Range:",
                    min_value=area_min,
                    max_value=area_max,
                    value=(area_min, area_max),
                    step=1,
                    format="%d",
                    key="area_slider"
                )
                # Display the selected range with formatting
                st.write(f"Selected: {area_range[0]:,} - {area_range[1]:,}")
        else:
            st.warning("No valid Area data found")
            area_range = (0, 0)
    
        # Absolute value change filter
        st.subheader("Absolute Value Change")
        abs_clean = df['absolute_value_change'].dropna()
        if len(abs_clean) > 0:
            abs_min, abs_max = int(abs_clean.min()), int(abs_clean.max())
            if abs_min == abs_max:
                abs_range = (abs_min, abs_max)
                st.write(f"All stores have the same absolute change: {abs_min:,}")
            else:
                abs_range = st.slider(
                    "Select Absolute Value Change Range:",
                    min_value=abs_min,
                    max_value=abs_max,
                    value=(abs_min, abs_max),
                    step=1,
                    format="%d",
                    key="abs_change_slider"
                )
                # Display the selected range with formatting
                st.write(f"Selected: {abs_range[0]:,} - {abs_range[1]:,}")
        else:
            st.warning("No valid Absolute Value Change data found")
            abs_range = (0, 0)
        
        # Percentage value change filter
        st.subheader("Percentage Value Change")
        pct_clean = df['percentage_value_change'].dropna()
        if len(pct_clean) > 0:
            pct_min, pct_max = float(pct_clean.min()), float(pct_clean.max())
            if pct_min == pct_max:
                pct_range = (pct_min, pct_max)
                st.write(f"All stores have the same percentage change: {pct_min}%")
            else:
                pct_range = st.slider(
                    "Select Percentage Value Change Range:",
                    min_value=pct_min,
                    max_value=pct_max,
                    value=(pct_min, pct_max),
                    step=max((pct_max - pct_min) / 100, 0.01),
                    key="pct_change_slider"
                )
        else:
            st.warning("No valid Percentage Value Change data found")
            pct_range = (0, 0)
    

    # Location filters in sidebar expander
    with st.sidebar.expander("🌍 Location Filters", expanded=False):  
        # Country filter - depends on operator and entity selection
        st.subheader("Country")
        
        # Filter countries based on operator and entity selection
        country_filter_df = df.copy()
        
        if selected_operator != 'All':
            country_filter_df = country_filter_df[country_filter_df['operator_name'] == selected_operator]
        
        if selected_entity != 'All':
            country_filter_df = country_filter_df[country_filter_df['entity'] == selected_entity]
        
        available_countries = country_filter_df['country'].unique().tolist()
        countries = ['All'] + sorted(available_countries)
        selected_country = st.radio("Select Country:", countries, key="country_radio")
        
        # City filter - depends on country, operator, and entity selection
        st.subheader("City")
        
        # Filter cities based on country, operator, and entity selection
        city_filter_df = df.copy()
        
        if selected_country != 'All':
            city_filter_df = city_filter_df[city_filter_df['country'] == selected_country]
        
        if selected_operator != 'All':
            city_filter_df = city_filter_df[city_filter_df['operator_name'] == selected_operator]
        
        if selected_entity != 'All':
            city_filter_df = city_filter_df[city_filter_df['entity'] == selected_entity]
        
        available_cities = city_filter_df['city'].unique().tolist()
        cities = ['All'] + sorted(available_cities)
        selected_city = st.radio("Select City:", cities, key="city_radio")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_country != 'All':
        filtered_df = filtered_df[filtered_df['country'] == selected_country]
    
    if selected_operator != 'All':
        filtered_df = filtered_df[filtered_df['operator_name'] == selected_operator]
    
    if selected_entity != 'All':
        filtered_df = filtered_df[filtered_df['entity'] == selected_entity]
    
    if selected_city != 'All':
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    
    if selected_tenure != 'All':
        filtered_df = filtered_df[filtered_df['Tenure'] == selected_tenure]
    
    # Apply Area filter only if we have valid data
    if len(area_clean) > 0:
        filtered_df = filtered_df[
            (filtered_df['Area'] >= area_range[0]) & 
            (filtered_df['Area'] <= area_range[1]) &
            (filtered_df['Area'].notna())
        ]
    
    # Apply Absolute Value Change filter only if we have valid data
    if len(abs_clean) > 0:
        filtered_df = filtered_df[
            (filtered_df['absolute_value_change'] >= abs_range[0]) & 
            (filtered_df['absolute_value_change'] <= abs_range[1]) &
            (filtered_df['absolute_value_change'].notna())
        ]
    
    # Apply Percentage Value Change filter only if we have valid data
    if len(pct_clean) > 0:
        filtered_df = filtered_df[
            (filtered_df['percentage_value_change'] >= pct_range[0]) & 
            (filtered_df['percentage_value_change'] <= pct_range[1]) &
            (filtered_df['percentage_value_change'].notna())
        ]
    
    # Display filtered data info
    st.info(f"Showing {len(filtered_df)} of {len(df)} stores")
    
    # Create the map
    if len(filtered_df) > 0:
        # Calculate center of map based on filtered data
        center_lat = filtered_df['latitude'].mean()
        center_lon = filtered_df['longitude'].mean()
        
        # Create folium map with CartoDB Positron tiles
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=6,
            tiles='CartoDB Positron'
        )
            
        # Add markers for each store
        for idx, row in filtered_df.iterrows():
            # Create popup content
            popup_content = f"""
            <div style="width: 250px;">
                <h4>{row['storename']}</h4>
                <p><strong>Operator:</strong> {row['operator_name']}</p>
                <p><strong>Entity:</strong> {row['entity']}</p>
                <p><strong>Value 2024:</strong> {row['value_2024']:,}</p>
                <p><strong>Value 2025:</strong> {row['value_2025']:,}</p>
                <p><strong>Absolute Change:</strong> {row['absolute_value_change']:,}</p>
                <p><strong>Percentage Change:</strong> {row['percentage_value_change']:.2f}%</p>
            </div>
            """
            
            # Determine marker color based on percentage change
            if row['percentage_value_change'] > 0:
                color = 'green'
                icon_color = 'white'
            elif row['percentage_value_change'] < 0:
                color = 'red'
                icon_color = 'white'
            else:
                color = 'gray'
                icon_color = 'white'
            
            # Add marker
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['storename'],
                icon=folium.Icon(color=color, icon_color=icon_color, icon='info-sign')
            ).add_to(m)
            
        # Display the map
        map_data = st_folium(m, width=None, height=500, returned_objects=[])
        
        # Legend
        st.markdown("""🟢 Value Increase 🔴 Value Decrease ⚫ No change""")
        
    else:
        st.warning("No stores match the selected filters.")
    
    # Display summary statistics
    if len(filtered_df) > 0:
        st.subheader("Summary Statistics")
        
        col1, col2, col3, col4 = st.columns([1,3,3,3])
        
        with col1:
            st.metric("Stores", len(filtered_df))
        
        with col2:
            sum_2024 = filtered_df['value_2024'].sum()
            st.metric("2024 Value", f"{sum_2024:,}")
        
        with col3:
            sum_abs_change = filtered_df['absolute_value_change'].sum()
            sign = "+" if sum_abs_change >= 0 else ""
            st.metric("Value Change", f"{sign}{sum_abs_change:,}")
        
        with col4:
            sum_2025 = filtered_df['value_2025'].sum()
            st.metric("2025 Value", f"{sum_2025:,}")
        
        # Show filtered data table (optional)
        if st.checkbox("Show Data Table"):
            df_display = filtered_df[DISPLAY_COLUMNS].copy()
            df_display.columns = DISPLAY_COLUMNS_DISPLAY_NAMES
            
            # Ensure proper data types for display to avoid Arrow serialization issues
            for i, col in enumerate(df_display.columns):
                if i == 0:  # Store name column - ensure it's string
                    df_display[col] = df_display[col].astype(str)
                else:  # Numeric columns - ensure they're numeric format as strings
                    df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0)
                    df_display[col] = df_display[col].apply(lambda x: f"{int(x):,}")
            
            # Add CSS for center alignment - most aggressive approach
            st.markdown("""
            <style>
                /* Force center alignment with maximum specificity */
                .stDataFrame div[data-testid="stDataFrame"] table td:nth-child(2),
                .stDataFrame div[data-testid="stDataFrame"] table td:nth-child(3), 
                .stDataFrame div[data-testid="stDataFrame"] table td:nth-child(4),
                .stDataFrame div[data-testid="stDataFrame"] table th:nth-child(2),
                .stDataFrame div[data-testid="stDataFrame"] table th:nth-child(3),
                .stDataFrame div[data-testid="stDataFrame"] table th:nth-child(4) {
                    text-align: center !important;
                    justify-content: center !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Wrap the dataframe in a container with a class
            with st.container():
                st.markdown('<div class="stDataFrame">', unsafe_allow_html=True)
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

else:
    # No data loaded - show upload instructions
    if not st.session_state.file_uploaded:
        st.info("👆 Please upload a CSV file to get started.")
        st.write("**File upload tips:**")
        st.write("- Only CSV files are accepted")
        st.write("- File should contain all required columns")
        st.write("- Maximum file size depends on your Streamlit configuration")
        
        # Show sample data format
        st.subheader("Expected CSV Format:")
        sample_data = pd.DataFrame({
            'storename': ['Store A', 'Store B', 'Store C'],
            'operator_name': ['Operator 1', 'Operator 2', 'Operator 1'],
            'entity': ['Entity A', 'Entity B', 'Entity C'],
            'country': ['USA', 'Canada', 'USA'],
            'city': ['New York', 'Toronto', 'Los Angeles'],
            'latitude': [40.7128, 43.6532, 34.0522],
            'longitude': [-74.0060, -79.3832, -118.2437],
            'value_2024': [100000, 150000, 80000],
            'value_2025': [120000, 140000, 95000],
            'absolute_value_change': [20000, -10000, 15000],
            'percentage_value_change': [20.0, -6.67, 18.75],
            'Tenure': ['Owned', 'Leased', 'Owned'],
            'Area': [2500, 3200, 1800]
        })
        
        st.dataframe(sample_data, use_container_width=True)
