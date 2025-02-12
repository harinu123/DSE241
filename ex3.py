import json
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_plotly_events import plotly_events
import requests

# -------------------------------
# Data Loading and Preparation
# -------------------------------

# Load the CO₂ emissions and population data.
df = pd.read_csv("co2-population.csv")

# --- Alternative GeoJSON ---
# We load a publicly available GeoJSON file that contains US state boundaries.
# This GeoJSON uses the state postal abbreviations (e.g., "AL", "AK", etc.) as the "id" field.
geojson_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
response = requests.get(geojson_url)
us_states_geojson = response.json()

# Create a mapping of full state names to postal abbreviations.
state_to_abbrev = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY"
}

# Add a new column to the DataFrame with the state postal abbreviations.
df["state_abbrev"] = df["State"].map(state_to_abbrev)

# -------------------------------
# Streamlit App Layout and Controls
# -------------------------------

st.set_page_config(page_title="US CO₂ Emissions & Population Dashboard", layout="wide")
st.title("US CO₂ Emissions & Population Dashboard")

st.sidebar.header("Controls")

# Select the data sector: emissions from various sectors or Population.
sector_options = sorted(df["Sector"].unique())
selected_sector = st.sidebar.selectbox("Select Sector:", options=sector_options, index=0)

# For the Population data, we use only the available years (if they differ)
if selected_sector == "Population":
    available_years = sorted(df[df["Sector"] == "Population"]["Year"].unique())
    selected_year = st.sidebar.selectbox("Select Year:", options=available_years, index=0)
else:
    year_min = int(df["Year"].min())
    year_max = int(df["Year"].max())
    selected_year = st.sidebar.slider("Select Year:", min_value=year_min, max_value=year_max, value=year_min, step=1)

# -------------------------------
# Create the Choropleth Map
# -------------------------------

# Filter the data for the chosen sector and year.
filtered_df = df[(df["Sector"] == selected_sector) & (df["Year"] == selected_year)]

if filtered_df.empty:
    st.warning("No data available for the selected sector and year.")
else:
    # For Population data, fix the color range based on the full available population range.
    if selected_sector == "Population":
        pop_df = df[df["Sector"] == "Population"]
        color_range = [pop_df["Value"].min(), pop_df["Value"].max()]
    else:
        color_range = [filtered_df["Value"].min(), filtered_df["Value"].max()]

    # Create the choropleth map.
    fig_map = px.choropleth(
        data_frame=filtered_df,
        geojson=us_states_geojson,
        locations="state_abbrev",   # Use the state abbreviations.
        color="Value",
        color_continuous_scale="Viridis",
        range_color=color_range,
        scope="usa",
        hover_name="State",
        labels={"Value": selected_sector},
        custom_data=["state_abbrev"]  # This will help us capture which state was clicked.
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        clickmode="event+select"
    )

    st.subheader(f"{selected_sector} Data for {selected_year}")
    st.write("Click on a state in the map to view its time series data.")

    # Use streamlit-plotly-events to capture click events on the map.
    selected_points = plotly_events(fig_map, click_event=True, hover_event=False, override_height=600)

    # -------------------------------
    # Create the Time Series Plot for the Selected State
    # -------------------------------
    st.subheader("Time Series for Selected State")

    if selected_points:
        # Extract the state abbreviation from the clicked point.
        custom_data = selected_points[0].get("customdata")
        if custom_data:
            state_abbrev_clicked = custom_data[0]
            # Find the full state name from the mapping dictionary.
            state_name = next((name for name, abbrev in state_to_abbrev.items() if abbrev == state_abbrev_clicked), None)
            if state_name:
                # Filter the data for this state (all years for the selected sector).
                state_df = df[(df["State"] == state_name) & (df["Sector"] == selected_sector)]
                fig_ts = px.line(
                    state_df,
                    x="Year",
                    y="Value",
                    markers=True,
                    title=f"{selected_sector} Trend for {state_name}",
                    labels={"Value": selected_sector, "Year": "Year"}
                )
                # For Population data, format the y-axis with commas.
                if selected_sector == "Population":
                    fig_ts.update_layout(yaxis_tickformat=",")
                fig_ts.update_layout(template="plotly_white")
                st.plotly_chart(fig_ts, use_container_width=True)
            else:
                st.warning("State not found from clicked data.")
        else:
            st.info("Click on a state to view its time series data.")
    else:
        st.info("Click on a state in the map above to view its time series data.")
