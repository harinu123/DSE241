import streamlit as st
import pandas as pd
import json
import plotly.express as px

# Set up the page configuration for a wide dashboard
st.set_page_config(page_title="US CO₂ Emissions & Population Dashboard", layout="wide")

# Title and introduction
st.title("U.S. CO₂ Emissions & Population Dashboard")
st.markdown("""
This dashboard enables you to explore state-level CO₂ emissions data (by sector) alongside population data for U.S. states, spanning 1990 to 2010.
Use the controls in the sidebar to:
- **Map View**: Visualize the spatial distribution of emissions or population for a chosen year.
- **Trend Analysis**: Examine temporal trends for selected states and sectors.
The goal is to answer questions like:
- *How do emissions differ by state in a given year?*
- *How have CO₂ emissions or population changed over time in key states?*
""")

# Function to load data (CSV and GeoJSON)
@st.cache_data
def load_data():
    # Load CSV data with CO₂ emissions and population by state
    df = pd.read_csv("co2-population.csv")
    # Load GeoJSON for US state boundaries
    with open("us-states.json") as f:
        states_geo = json.load(f)
    return df, states_geo

df, states_geo = load_data()

# Create a mapping from state name to FIPS code using the GeoJSON features
state_to_fips = {feature["properties"]["name"]: feature["id"] for feature in states_geo["features"]}
df["fips"] = df["State"].map(state_to_fips)

# Sidebar controls for visualization selection
st.sidebar.title("Visualization Settings")
viz_type = st.sidebar.radio("Choose Visualization Type", ["Map View", "Trend Analysis"])

if viz_type == "Map View":
    st.sidebar.header("Map Filters")
    # Select a year between the min and max available in the data
    selected_year = st.sidebar.slider("Select Year", 
                                      min_value=int(df["Year"].min()), 
                                      max_value=int(df["Year"].max()), 
                                      value=int(df["Year"].min()))
    # Allow selection of the sector (emissions category or population)
    sectors = sorted(df["Sector"].unique().tolist())
    selected_sector = st.sidebar.selectbox("Select Sector", sectors)
    
    # Filter the dataframe for the chosen year and sector
    df_map = df[(df["Year"] == selected_year) & (df["Sector"] == selected_sector)]
    
    st.subheader(f"Choropleth Map: {selected_sector} in {selected_year}")
    fig_map = px.choropleth(
        df_map,
        geojson=states_geo,
        locations="fips",
        color="Value",
        color_continuous_scale="Viridis",
        scope="usa",
        hover_name="State",
        hover_data={"fips": False, "Year": True, "Value": True},
        labels={"Value": f"{selected_sector} {'Population' if selected_sector=='Population' else 'Emissions (million metric tons CO₂)'}"}
    )
    fig_map.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    st.plotly_chart(fig_map, use_container_width=True)

elif viz_type == "Trend Analysis":
    st.sidebar.header("Trend Analysis Filters")
    sectors = sorted(df["Sector"].unique().tolist())
    selected_sector = st.sidebar.selectbox("Select Sector for Trend", sectors)
    states_list = sorted(df["State"].unique().tolist())
    selected_states = st.sidebar.multiselect("Select States", states_list, default=["California", "Texas", "New York"])
    
    # Filter the data for selected states and sector
    df_trend = df[(df["Sector"] == selected_sector) & (df["State"].isin(selected_states))]
    
    st.subheader(f"Trend Analysis: {selected_sector} Over Time")
    fig_trend = px.line(
        df_trend,
        x="Year",
        y="Value",
        color="State",
        markers=True,
        labels={"Value": f"{selected_sector} {'Population' if selected_sector=='Population' else 'Emissions (million metric tons CO₂)'}", "Year": "Year"}
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")
st.markdown("### About This Dashboard")
st.markdown("""
This interactive dashboard was developed in **Streamlit** to provide a flexible, easy-to-use interface for exploring CO₂ emissions and population trends across U.S. states. Its advantages include:
- **Interactivity**: Quickly filter data by year, sector, and state.
- **Integrated spatial analysis**: Use choropleth maps to view geographic patterns.
- **Temporal trends**: Examine how metrics evolve over time with dynamic line charts.
Such visualizations not only help answer key environmental and demographic questions but also enable further exploration and augmentation with additional data sources.
""")
