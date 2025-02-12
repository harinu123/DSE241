import json
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_plotly_events import plotly_events

# -------------------------------
# Data Loading and Preparation
# -------------------------------
# Read the CO₂ emissions and population CSV file.
df = pd.read_csv("co2-population.csv")

# Load the GeoJSON file for U.S. state boundaries.
with open("us-states.json") as f:
    us_states = json.load(f)

# Mapping of state names to FIPS codes (needed for linking with the GeoJSON).
state_fips = {
    "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05",
    "California": "06", "Colorado": "08", "Connecticut": "09", "Delaware": "10",
    "Florida": "12", "Georgia": "13", "Hawaii": "15", "Idaho": "16",
    "Illinois": "17", "Indiana": "18", "Iowa": "19", "Kansas": "20",
    "Kentucky": "21", "Louisiana": "22", "Maine": "23", "Maryland": "24",
    "Massachusetts": "25", "Michigan": "26", "Minnesota": "27", "Mississippi": "28",
    "Missouri": "29", "Montana": "30", "Nebraska": "31", "Nevada": "32",
    "New Hampshire": "33", "New Jersey": "34", "New Mexico": "35", "New York": "36",
    "North Carolina": "37", "North Dakota": "38", "Ohio": "39", "Oklahoma": "40",
    "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45",
    "South Dakota": "46", "Tennessee": "47", "Texas": "48", "Utah": "49",
    "Vermont": "50", "Virginia": "51", "Washington": "53", "West Virginia": "54",
    "Wisconsin": "55", "Wyoming": "56"
}

# Add a column for FIPS codes (used by the GeoJSON).
df["fips"] = df["State"].map(state_fips)

# -------------------------------
# Streamlit App Layout and Controls
# -------------------------------
st.set_page_config(page_title="US CO₂ Emissions & Population Dashboard", layout="wide")
st.title("US CO₂ Emissions & Population Dashboard")

st.sidebar.header("Controls")
sector_options = sorted(df["Sector"].unique())
selected_sector = st.sidebar.selectbox("Select Sector:", options=sector_options, index=0)

# For Population, use only the available years (in case population data is not available for every year)
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
# Filter the dataset for the selected sector and year.
filtered_df = df[(df["Sector"] == selected_sector) & (df["Year"] == selected_year)]

if filtered_df.empty:
    st.warning("No data available for the selected sector and year.")
else:
    # For Population, set the color range based on the full population range across all years
    if selected_sector == "Population":
        pop_df = df[df["Sector"] == "Population"]
        color_range = [pop_df["Value"].min(), pop_df["Value"].max()]
    else:
        color_range = [filtered_df["Value"].min(), filtered_df["Value"].max()]

    # Create the choropleth map.
    fig_map = px.choropleth(
        data_frame=filtered_df,
        geojson=us_states,
        locations="fips",         # Link states via FIPS codes.
        color="Value",
        color_continuous_scale="Viridis",
        range_color=color_range,
        scope="usa",
        hover_name="State",
        labels={"Value": selected_sector},
        custom_data=["fips"]      # Needed to capture click events.
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.subheader(f"{selected_sector} Data for {selected_year}")
    st.write("Click on a state to view its time series data.")

    # Capture click events on the map using streamlit-plotly-events.
    selected_points = plotly_events(fig_map, click_event=True, hover_event=False, override_height=600)

    # -------------------------------
    # Create the Time Series Plot for the Selected State
    # -------------------------------
    st.subheader("Time Series for Selected State")
    if selected_points:
        # Extract the FIPS code from the clicked point.
        fips_clicked = selected_points[0].get("customdata")
        if fips_clicked:
            fips_code = fips_clicked[0]
            # Look up the corresponding state name.
            state_name = next((name for name, code in state_fips.items() if code == fips_code), None)
            if state_name:
                # Filter data for the clicked state (across all available years for the selected sector).
                state_df = df[(df["State"] == state_name) & (df["Sector"] == selected_sector)]
                fig_ts = px.line(
                    state_df,
                    x="Year",
                    y="Value",
                    markers=True,
                    title=f"{selected_sector} Trend for {state_name}",
                    labels={"Value": selected_sector, "Year": "Year"}
                )
                # For Population, format the y-axis for better readability.
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
