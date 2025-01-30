import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For map background (world_110m)

@st.cache_data
def load_data():
    df = pd.read_json("olympics.json")
    return df

def main():
    # Streamlit page config
    st.set_page_config(
        page_title="Winter Olympics Medal Explorer", 
        layout="wide"
    )
    st.title("Winter Olympics Medal Explorer (1924 – 2006)")

    # 1) Load data
    df = load_data()

    # 2) Sidebar Filters
    st.sidebar.header("1) Data Filters")

    # Year range slider
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

    st.sidebar.markdown(f"**Records after filtering:** {len(filtered_df)}")

    # 3) Aggregations
    # (A) Medal counts by year & country
    medal_by_year_country = (
        filtered_df
        .groupby(["Year", "Country"])
        .size()
        .reset_index(name="MedalsWon")
    )

    # (B) Medal distribution by year & medal type
    medal_distribution = (
        filtered_df
        .groupby(["Year", "Medal"])
        .size()
        .reset_index(name="Count")
    )

    # (C) Medal breakdown by country & medal type
    medal_by_country_type = (
        filtered_df
        .groupby(["Country", "Medal"])
        .size()
        .reset_index(name="Count")
    )

    # (D) City-based summary for map
    city_summary = (
        filtered_df
        .groupby(["Year", "City", "Latitude", "Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # 4) Interactive Area Chart + Stacked Bar
    st.markdown("### 1) Interactive Medal Counts over Time (Brushing to Filter)")

    # Brush for years
    year_brush = alt.selection_interval(encodings=["x"])

    # Total medals by year (for area chart)
    total_medals_by_year = (
        filtered_df
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    area_chart = (
        alt.Chart(total_medals_by_year)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("TotalMedals:Q", title="Total Medals"),
            tooltip=["Year", "TotalMedals"]
        )
        .properties(width=500, height=250)
        .add_selection(year_brush)
    )

    # Stacked bar for medal distribution, filtered by brush
    distribution_chart = (
        alt.Chart(medal_distribution)
        .mark_bar()
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("Count:Q", stack="normalize", title="Proportion of Medals"),
            color=alt.Color("Medal:N", legend=alt.Legend(title="Medal Type")),
            tooltip=["Year", "Medal", "Count"]
        )
        .transform_filter(year_brush)
        .properties(width=500, height=250)
    )

    col1, col2 = st.columns([1,1])
    with col1:
        st.altair_chart(area_chart, use_container_width=True)
    with col2:
        st.altair_chart(distribution_chart, use_container_width=True)

    # 5) Bubble Chart (Year vs Country), sized by medals
    st.markdown("### 2) Bubble Chart (Year vs. Country) with Selection")

    # Single selection of a bubble
    year_country_select = alt.selection_single(
        fields=["Year", "Country"],
        empty="none"  # If nothing is selected, we get no data in the breakdown
    )

    bubble_chart = (
        alt.Chart(medal_by_year_country)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", scale=alt.Scale(range=[0,1000]), legend=alt.Legend(title="Medals")),
            color=alt.condition(year_country_select, alt.value("firebrick"), alt.value("steelblue")),
            tooltip=["Year", "Country", "MedalsWon"]
        )
        .add_selection(year_country_select)
        .properties(width=700, height=500)
        .interactive()
    )

    st.write("**Select a bubble to see that Country-Year's Medal Breakdown**")
    st.altair_chart(bubble_chart, use_container_width=True)

    # Medal breakdown bar chart for selected bubble
    st.markdown("#### Medal Breakdown for Selected Bubble")
    breakdown_src = (
        filtered_df
        .groupby(["Year", "Country", "Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    breakdown_chart = (
        alt.Chart(breakdown_src)
        .mark_bar()
        .encode(
            x=alt.X("Medal:N", sort=["Gold","Silver","Bronze"]),
            y=alt.Y("NumMedals:Q", title="Number of Medals"),
            color=alt.Color("Medal:N"),
            tooltip=["Year","Country","Medal","NumMedals"]
        )
        .transform_filter(year_country_select)
        .properties(width=300, height=300)
    )

    st.altair_chart(breakdown_chart, use_container_width=False)

    # 6) Map View: Host cities, filtered by the year brush
    st.markdown("### 3) Host City Map (Filtered by Brushed Years)")

    world_map = alt.topo_feature(data.world_110m.url, feature='countries')

    # Base map
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
            tooltip=["City","Year","CityMedals"]
        )
        .transform_filter(year_brush)
    )

    city_map = map_background + city_points
    st.altair_chart(city_map, use_container_width=True)

    # 7) Data Table
    with st.expander("View Filtered Data Table"):
        st.write("Below is the raw data table after applying the filters:")
        st.dataframe(filtered_df)

    st.markdown("---")
    st.markdown(
        "**Hint:** 1) Brush a range of years in the area chart. "
        "2) Notice how the stacked bar below it updates to only those brushed years. "
        "3) Then click a bubble (year/country) to see the medal breakdown for that selection. "
        "4) The map also updates to the brushed years!"
    )

if __name__ == "__main__":
    main()
