import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

st.title("West Nile Virus in California Counties")

# 1) Load CSV Data
df = pd.read_csv("West_Nile_Virus_by_County.csv")

# Make sure the CSV has the necessary columns
required_cols = {"Year", "Week_Reported", "County", "id", "Positive_Cases"}
if not required_cols.issubset(df.columns):
    st.error(f"CSV must contain columns: {required_cols}")
    st.stop()

# 2) Let user pick a year in the sidebar
years = sorted(df["Year"].unique())
selected_year = st.sidebar.selectbox("Select Year", years, index=0)

# 3) Filter data for the selected year
year_df = df[df["Year"] == selected_year]

# 4) Aggregate total Positive_Cases by county for the selected year
county_agg = year_df.groupby("id", as_index=False)["Positive_Cases"].sum()

# 5) Load US counties geometry from vega_datasets
counties = alt.topo_feature(data.us_10m.url, "counties")

# 6) Choropleth Map for California
map_chart = (
    alt.Chart(counties)
    .mark_geoshape(stroke="white")
    .transform_calculate(
        # state_fips = floor( id / 1000 ), 
        # so we can filter to show only state_fips == 6 (California)
        state_fips="floor(datum.id / 1000)"
    )
    .transform_filter(
        alt.datum.state_fips == 6  # Keep only California counties
    )
    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(county_agg, key="id", fields=["Positive_Cases"])
    )
    .encode(
        # Color counties by total Positive_Cases
        color=alt.Color("Positive_Cases:Q", 
                        title="Total Cases",
                        scale=alt.Scale(scheme="reds")),
        # Tooltip shows the numeric value on hover
        tooltip=[alt.Tooltip("Positive_Cases:Q", title="Total Cases")]
    )
    .properties(width=600, height=400, title=f"Total WNV Cases by County ({selected_year})")
    .project("albersUsa")
)

# 7) Time-Series Chart of Weekly Positive Cases
time_series = (
    alt.Chart(year_df)
    .mark_line(point=True)
    .encode(
        x=alt.X("Week_Reported:O", title="Epidemiological Week"),
        y=alt.Y("Positive_Cases:Q", title="Positive Cases"),
        color="County:N",
        tooltip=["County:N", "Week_Reported:O", "Positive_Cases:Q"]
    )
    .properties(width=600, height=300, title=f"Weekly Positive Cases by County ({selected_year})")
    .interactive()
)

# 8) Display both charts and data
st.altair_chart(map_chart, use_container_width=True)
st.altair_chart(time_series, use_container_width=True)

st.subheader(f"Data for {selected_year}")
st.write(year_df)
