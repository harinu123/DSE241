import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For a simple world map background

# -------------------------------------------------------------------
# 1) DATA LOADING
# -------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_json("olympics.json")
    return df

def main():
    st.set_page_config(page_title="Winter Olympics Explorer", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006)")

    # Load data
    df = load_data()

    # -------------------------------------------------------------------
    # 2) SIDEBAR CONTROLS
    # -------------------------------------------------------------------
    st.sidebar.header("Filters")

    # Year
    all_years = sorted(df["Year"].unique())
    min_year, max_year = st.sidebar.select_slider(
        "Select Year Range:",
        options=all_years,
        value=(min(all_years), max(all_years))
    )

    # Sport
    sports = sorted(df["Sport"].unique())
    selected_sports = st.sidebar.multiselect(
        "Select Sports:",
        options=sports,
        default=sports
    )

    # Country
    countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries:",
        options=countries,
        default=countries
    )

    # Gender
    gender_options = ["M", "W", "X"]
    selected_genders = st.sidebar.multiselect(
        "Select Genders:",
        options=gender_options,
        default=gender_options
    )

    # Filter DataFrame
    filtered_df = df[
        (df["Year"] >= min_year) &
        (df["Year"] <= max_year) &
        (df["Sport"].isin(selected_sports)) &
        (df["Country"].isin(selected_countries)) &
        (df["Gender"].isin(selected_genders))
    ]

    st.sidebar.write(f"**Filtered Rows:** {len(filtered_df)}")

    # -------------------------------------------------------------------
    # 3) AGGREGATIONS
    # -------------------------------------------------------------------
    # (A) Total medals by year
    total_medals_by_year = (
        filtered_df
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    # (B) Medal distribution by year & medal type
    medal_distribution = (
        filtered_df
        .groupby(["Year", "Medal"])
        .size()
        .reset_index(name="Count")
    )

    # (C) Year-Country medal counts (for bubble chart)
    year_country_medals = (
        filtered_df
        .groupby(["Year","Country"])
        .size()
        .reset_index(name="MedalsWon")
    )

    # (D) Breakdown by (Year, Country, Medal)
    breakdown_df = (
        filtered_df
        .groupby(["Year","Country","Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    # (E) City-based summary for map
    city_summary = (
        filtered_df
        .groupby(["Year", "City", "Latitude", "Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # -------------------------------------------------------------------
    # 4) AREA CHART (with BRUSH) + STACKED BAR + MAP
    # -------------------------------------------------------------------
    st.subheader("1) Total Medals Over Time (Brush the Year Range)")

    # Brush selection across 'x' (years)
    year_brush = alt.selection_interval(encodings=["x"])

    # Area Chart: total medals by year
    area_chart = (
        alt.Chart(total_medals_by_year)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("TotalMedals:Q", title="Total Medals"),
            tooltip=["Year","TotalMedals"]
        )
        .add_selection(year_brush)
        .properties(width=500, height=250)
    )

    # Stacked Bar: medal distribution by year
    stacked_bar = (
        alt.Chart(medal_distribution)
        .mark_bar()
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("Count:Q", stack="normalize", title="Proportion of Medals"),
            color=alt.Color("Medal:N", legend=alt.Legend(title="Medal")),
            tooltip=["Year","Medal","Count"]
        )
        .transform_filter(year_brush)
        .properties(width=500, height=250)
    )

    col1, col2 = st.columns([1,1])
    with col1:
        st.altair_chart(area_chart, use_container_width=True)
    with col2:
        st.altair_chart(stacked_bar, use_container_width=True)

    st.subheader("2) Host City Map (Filtered by Brushed Years)")
    world_map = alt.topo_feature(data.world_110m.url, feature='countries')

    # Background
    map_background = (
        alt.Chart(world_map)
        .mark_geoshape(fill="lightgray", stroke="white")
        .properties(width=700, height=400)
        .project("naturalEarth1")
    )

    # Circles for host cities
    city_points = (
        alt.Chart(city_summary)
        .mark_circle(opacity=0.6, color="red")
        .encode(
            longitude="Longitude:Q",
            latitude="Latitude:Q",
            size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0,1000])),
            tooltip=["City","Year","CityMedals"]
        )
        .transform_filter(year_brush)  # Filter to the brushed years
    )

    city_map = map_background + city_points
    st.altair_chart(city_map, use_container_width=True)

    # -------------------------------------------------------------------
    # 5) BUBBLE CHART + SINGLE SELECTION → MEDAL BREAKDOWN
    # -------------------------------------------------------------------
    st.subheader("3) Bubble Chart of (Year vs. Country)")

    # Single selection on Year+Country
    year_country_sel = alt.selection_single(fields=["Year","Country"])

    # Bubble chart
    bubble_chart = (
        alt.Chart(year_country_medals)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", sort=all_years),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", scale=alt.Scale(range=[0,1000])),
            color=alt.Color("Year:O", legend=None),  # Color by Year to avoid param usage
            tooltip=["Year","Country","MedalsWon"]
        )
        .add_selection(year_country_sel)
        .properties(width=700, height=400)
    )

    st.write("**Click on a bubble to see medal breakdown for that (year, country).**")
    st.altair_chart(bubble_chart, use_container_width=True)

    st.subheader("4) Medal Breakdown for Selected Bubble")

    breakdown_chart = (
        alt.Chart(breakdown_df)
        .mark_bar()
        .encode(
            x=alt.X("Medal:N", sort=["Gold","Silver","Bronze"]),
            y=alt.Y("NumMedals:Q", title="Number of Medals"),
            color=alt.Color("Medal:N"),
            tooltip=["Year","Country","Medal","NumMedals"]
        )
        .transform_filter(year_country_sel)
        .properties(width=300, height=300)
    )

    st.altair_chart(breakdown_chart, use_container_width=False)

    # -------------------------------------------------------------------
    # 6) Data Table
    # -------------------------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.dataframe(filtered_df)

    st.markdown("---")
    st.markdown(
        "**Usage tips:**\n"
        "1. Brush across the **area chart** to filter by a year range → notice updates in the stacked bar & map.\n"
        "2. **Click** a bubble in the bubble chart to see that (year,country)'s medal breakdown."
    )

if __name__ == "__main__":
    main()
