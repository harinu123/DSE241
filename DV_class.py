import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For world map background

# -------------------------------------------------------------------
# 1) DATA LOADING AND PREPROCESSING
# -------------------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_json("olympics.json")
    # Correct any data anomalies if needed
    # Example: unify 'W' -> 'F' if you prefer F for female
    # df["Gender"] = df["Gender"].replace({"W": "F"})
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

    # (C) Medal breakdown by country & medal type (for stacked bar or donut)
    medal_by_country_type = (
        filtered_df
        .groupby(["Country", "Medal"])
        .size()
        .reset_index(name="Count")
    )

    # (D) Summaries for city-based map (host city, lat/lon, total medals that year)
    # Each record in the dataset is a medal awarded in that city/year. Summarize total medals in that city for each year.
    city_summary = (
        filtered_df
        .groupby(["Year", "City", "Latitude", "Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # -------------------------------------------------------------------
    # 4) ADVANCED INTERACTIVE CHARTS WITH ALT.SELECTION
    # -------------------------------------------------------------------
    st.markdown("### 1) Interactive Medal Counts over Time (Brushing to Filter)")

    # -- Create a brush for the Year dimension
    brush = alt.selection_interval(
        encodings=["x"],  # brush along the x-axis (Year)
        name="year_brush"
    )

    # ----- Chart A: LINE/AREA Chart of Total Medals by Year -----
    total_medals_by_year = (
        filtered_df
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    base_line = alt.Chart(total_medals_by_year).mark_area(opacity=0.6).encode(
        x=alt.X("Year:O", title="Year", sort=all_years),
        y=alt.Y("TotalMedals:Q", title="Total Medals"),
        tooltip=["Year", "TotalMedals"]
    ).properties(
        width=500, height=250
    )

    line_chart = base_line.add_selection(brush)

    # ----- Chart B: STACKED BAR - Medal Distribution by Year (Filtered by brush) -----
    distribution_chart = alt.Chart(medal_distribution).mark_bar().encode(
        x=alt.X("Year:O", title="Year", sort=all_years),
        y=alt.Y("Count:Q", stack='normalize', title="Proportion of Medals"),
        color=alt.Color("Medal:N", legend=alt.Legend(title="Medal Type")),
        tooltip=["Year", "Medal", "Count"]
    ).transform_filter(
        brush  # Only show data within the brushed Years
    ).properties(
        width=500, height=250
    )

    # Arrange side by side
    col1, col2 = st.columns([1,1])
    with col1:
        st.altair_chart(line_chart, use_container_width=True)
    with col2:
        st.altair_chart(distribution_chart, use_container_width=True)

    # -------------------------------------------------------------------
    # 5) BUBBLE CHART: YEAR vs. COUNTRY, SIZED BY MEDALS
    # -------------------------------------------------------------------
    st.markdown("### 2) Bubble Chart (Year vs. Country) with Selection")

    # We’ll create a single selection that picks a (year,country) pair
    # Then we’ll filter a second chart to only that pair for a medal breakdown.

    single_select = alt.selection_single(
        fields=["Year", "Country"],
        empty="none",  # If no selection, filter will be empty
        name="Select"
    )

    bubble_chart = (
        alt.Chart(medal_by_year_country)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", title="Year", sort=all_years),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", legend=alt.Legend(title="Medals Count"), scale=alt.Scale(range=[0, 1000])),
            color=alt.condition(single_select, alt.value("firebrick"), alt.value("steelblue")),
            tooltip=["Year", "Country", "MedalsWon"]
        )
        .add_selection(single_select)
        .properties(width=700, height=500)
        .interactive()
    )

    st.write("**Select a bubble to drill down into that Country-Year medal composition**")
    st.altair_chart(bubble_chart, use_container_width=True)

    # Once we select a (year,country), show a breakdown by Medal type
    # We'll filter the original data or an aggregated data with transform_filter
    st.markdown("#### Medal Breakdown for Selected Bubble")

    # Build an aggregated dataset with year, country, medal
    breakdown_src = (
        filtered_df
        .groupby(["Year", "Country", "Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    breakdown_chart = alt.Chart(breakdown_src).mark_bar().encode(
        x=alt.X("Medal:N", sort=["Gold", "Silver", "Bronze"]),
        y=alt.Y("NumMedals:Q", title="Number of Medals"),
        color=alt.Color("Medal:N"),
        tooltip=["Year", "Country", "Medal", "NumMedals"]
    ).transform_filter(
        single_select  # Filter to the single selected Year & Country
    ).properties(
        width=300, height=300
    )

    st.altair_chart(breakdown_chart, use_container_width=False)

    # -------------------------------------------------------------------
    # 6) MAP VIEW: HOST CITY LOCATIONS & MEDALS (Filtered by Year Brush)
    # -------------------------------------------------------------------
    st.markdown("### 3) Host City Map (Filtered by Year Brush)")

    # We'll use vega_datasets to get a world map background (simplified).
    world_map = alt.topo_feature(data.world_110m.url, feature='countries')

    # Base map chart
    map_background = (
        alt.Chart(world_map)
        .mark_geoshape(
            fill="lightgray", 
            stroke="white"
        )
        .properties(width=700, height=400)
        .project("naturalEarth1")
    )

    # We’ll plot the circles for the host cities (from city_summary),
    # filtered by the year brush used in the line chart above.
    city_points = (
        alt.Chart(city_summary)
        .mark_circle(opacity=0.6, color="red")
        .encode(
            longitude="Longitude:Q",
            latitude="Latitude:Q",
            size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0,1000])),
            tooltip=["City", "Year", "CityMedals"]
        )
        .transform_filter(brush)
    )

    # Combine background + circles
    city_map = map_background + city_points
    st.altair_chart(city_map, use_container_width=True)

    # -------------------------------------------------------------------
    # 7) DATA TABLE
    # -------------------------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.write("Below is the raw data table after applying the filters:")
        st.dataframe(filtered_df)

    st.markdown("---")
    st.markdown("**Tip**: Try brushing a range of years in the area chart at the top. "
                "Then select a bubble in the bubble chart to see the medal breakdown bar chart update. "
                "Also see how the map circles update with the brushed years!")


if __name__ == "__main__":
    main()
