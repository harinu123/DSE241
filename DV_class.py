import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For world map background

# -------------------------------------------------------------------
# 1) DATA LOADING AND PREPROCESSING
# -------------------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_json("/mnt/data/olympics.json")  # Ensure correct file path
    return df

def main():
    # Set page layout
    st.set_page_config(page_title="Winter Olympics Medal Explorer", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006)")

    # Load data
    df = load_data()

    # -------------------------------------------------------------------
    # 2) SIDEBAR CONTROLS
    # -------------------------------------------------------------------
    st.sidebar.header("1) Data Filters")

    # Year selection
    all_years = sorted(df["Year"].unique())
    min_year, max_year = st.sidebar.select_slider(
        "Select Year Range:",
        options=all_years,
        value=(min(all_years), max(all_years))
    )

    # Sport selection
    sports = sorted(df["Sport"].unique())
    selected_sports = st.sidebar.multiselect(
        "Select Sports:",
        options=sports,
        default=sports
    )

    # Country selection
    countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries:",
        options=countries,
        default=countries
    )

    # Gender selection
    gender_options = ["M", "W", "X"]
    selected_genders = st.sidebar.multiselect(
        "Select Genders:",
        options=gender_options,
        default=gender_options
    )

    # Filter the DataFrame
    filtered_df = df[
        (df["Year"] >= min_year) & 
        (df["Year"] <= max_year) &
        (df["Sport"].isin(selected_sports)) &
        (df["Country"].isin(selected_countries)) &
        (df["Gender"].isin(selected_genders))
    ]

    # Provide data summary
    st.sidebar.markdown(f"**Records after filtering:** {len(filtered_df)}")

    # -------------------------------------------------------------------
    # 3) CREATE AGGREGATIONS
    # -------------------------------------------------------------------
    medal_by_year_country = (
        filtered_df.groupby(["Year", "Country"]).size().reset_index(name="MedalsWon")
    )
    
    medal_distribution = (
        filtered_df.groupby(["Year", "Medal"]).size().reset_index(name="Count")
    )

    medal_by_country_type = (
        filtered_df.groupby(["Country", "Medal"]).size().reset_index(name="Count")
    )

    city_summary = (
        filtered_df.groupby(["Year", "City", "Latitude", "Longitude"])
        .size().reset_index(name="CityMedals")
    )

    # -------------------------------------------------------------------
    # 4) ALT.SELECTION OBJECTS
    # -------------------------------------------------------------------
    year_brush = alt.selection_interval(name="year_brush", encodings=["x"])
    select_single = alt.selection_single(name="Select", fields=["Year", "Country"], empty="none")

    # -------------------------------------------------------------------
    # 5) INTERACTIVE CHARTS
    # -------------------------------------------------------------------
    st.markdown("### 1) Interactive Medal Counts over Time")

    total_medals_by_year = (
        filtered_df.groupby("Year").size().reset_index(name="TotalMedals")
    )

    base_line = alt.Chart(total_medals_by_year).mark_area(opacity=0.6).encode(
        x=alt.X("Year:O", title="Year", sort=all_years),
        y=alt.Y("TotalMedals:Q", title="Total Medals"),
        tooltip=["Year", "TotalMedals"]
    ).properties(width=500, height=250).add_selection(year_brush)

    medal_dist_chart = alt.Chart(medal_distribution).mark_bar().encode(
        x=alt.X("Year:O", title="Year", sort=all_years),
        y=alt.Y("Count:Q", stack='normalize', title="Proportion of Medals"),
        color=alt.Color("Medal:N", legend=alt.Legend(title="Medal Type")),
        tooltip=["Year", "Medal", "Count"]
    ).transform_filter(year_brush).properties(width=500, height=250)

    col1, col2 = st.columns([1,1])
    with col1:
        st.altair_chart(base_line, use_container_width=True)
    with col2:
        st.altair_chart(medal_dist_chart, use_container_width=True)

    # -------------------------------------------------------------------
    # 6) BUBBLE CHART: YEAR vs. COUNTRY
    # -------------------------------------------------------------------
    st.markdown("### 2) Bubble Chart (Year vs. Country) with Selection")

    bubble_chart = (
        alt.Chart(medal_by_year_country)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", title="Year", sort=all_years),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", legend=alt.Legend(title="Medals Count")),
            color=alt.condition(select_single, alt.value("firebrick"), alt.value("steelblue")),
            tooltip=["Year", "Country", "MedalsWon"]
        )
        .add_selection(select_single)
        .properties(width=700, height=500)
    )

    st.altair_chart(bubble_chart, use_container_width=True)

    st.markdown("#### Medal Breakdown for Selected Country-Year")
    
    breakdown_src = (
        filtered_df.groupby(["Year", "Country", "Medal"]).size().reset_index(name="NumMedals")
    )

    breakdown_chart = alt.Chart(breakdown_src).mark_bar().encode(
        x=alt.X("Medal:N", sort=["Gold", "Silver", "Bronze"]),
        y=alt.Y("NumMedals:Q", title="Number of Medals"),
        color=alt.Color("Medal:N"),
        tooltip=["Year", "Country", "Medal", "NumMedals"]
    ).transform_filter(select_single).properties(width=300, height=300)

    st.altair_chart(breakdown_chart, use_container_width=False)

    # -------------------------------------------------------------------
    # 7) MAP VIEW: HOST CITY LOCATIONS & MEDALS
    # -------------------------------------------------------------------
    st.markdown("### 3) Host City Map (Filtered by Year Brush)")

    world_map = alt.topo_feature(data.world_110m.url, feature='countries')

    map_background = (
        alt.Chart(world_map)
        .mark_geoshape(fill="lightgray", stroke="white")
        .properties(width=700, height=400)
        .project("naturalEarth1")
    )

    city_points = (
        alt.Chart(city_summary)
        .mark_circle(opacity=0.6, color="red")
        .encode(
            longitude="Longitude:Q",
            latitude="Latitude:Q",
            size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0,1000])),
            tooltip=["City", "Year", "CityMedals"]
        )
        .transform_filter(year_brush)
    )

    city_map = map_background + city_points
    st.altair_chart(city_map, use_container_width=True)

    # -------------------------------------------------------------------
    # 8) DATA TABLE
    # -------------------------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
