import streamlit as st
import pandas as pd
import json
import plotly.express as px

st.set_page_config(page_title="US CO₂ Emissions & Population Dashboard", layout="wide")


st.title("U.S. CO₂ Emissions & Population Dashboard")
st.markdown("""
Exersize 3 for my DSE Data viz course
here is a dashboard that allows you to explore state-level CO₂ emissions data (by sector) alongside population data for U.S. states, spanning 1990 to 2010.
Use the controls in the sidebar to:
- **Map View**: Visualize the spatial distribution of emissions or population for a chosen year.
- **Trend Analysis**: Examine temporal trends for selected states and sectors.
The goal is to answer questions like:
- *How do emissions differ by state in a given year?*
- *How have CO₂ emissions or population changed over time in key states?*
""")


@st.cache_data
def load_data():

    df = pd.read_csv("co2-population.csv")

    with open("us-states.json") as f:
        states_geo = json.load(f)
    return df, states_geo

df, states_geo = load_data()


state_to_fips = {feature["properties"]["name"]: feature["id"] for feature in states_geo["features"]}
df["fips"] = df["State"].map(state_to_fips)


st.sidebar.title("Visualization Settings")
viz_type = st.sidebar.radio("Choose Visualization Type", ["Map View", "Trend Analysis"])

if viz_type == "Map View":
    st.sidebar.header("Map Filters")

    selected_year = st.sidebar.slider("Select Year", 
                                      min_value=int(df["Year"].min()), 
                                      max_value=int(df["Year"].max()), 
                                      value=int(df["Year"].min()))

    sectors = sorted(df["Sector"].unique().tolist())
    selected_sector = st.sidebar.selectbox("Select Sector", sectors)

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
st.markdown("### Aboutt")
st.markdown("""
Quickly filter data by year, sector, and state.
 Use choropleth maps to view geographic patterns.
 Examine how metrics evolve over time with dynamic line charts.
""")
