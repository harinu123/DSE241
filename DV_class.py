import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For world map background

@st.cache_data
def load_data():
    # Load the JSON data
    df = pd.read_json("olympics.json")
    return df

def main():
    st.set_page_config(page_title="Winter Olympics Explorer", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006)")

    # -------------------------------------------------------------------
    # 1) DATA LOADING & SIDEBAR FILTERS
    # -------------------------------------------------------------------
    df = load_data()

    st.sidebar.header("Data Filters")
    
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
    st.sidebar.markdown(f"**Records after filtering:** {len(filtered_df)}")

    # -------------------------------------------------------------------
    # 2) AGGREGATED DATA
    # -------------------------------------------------------------------
    # A) Total medals by year
    total_medals_by_year = (
        filtered_df
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    # B) Medal distribution by year & type
    medal_distribution = (
        filtered_df
        .groupby(["Year","Medal"])
        .size()
        .reset_index(name="Count")
    )

    # C) Country vs. year medal counts (for bubble chart)
    medal_by_year_country = (
        filtered_df
        .groupby(["Year", "Country"])
        .size()
        .reset_index(name="MedalsWon")
    )

    # D) Breakdown by (Year, Country, Medal)
    breakdown_src = (
        filtered_df
        .groupby(["Year","Country","Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    # E) City summary for map (host city, lat, lon, year)
    city_summary = (
        filtered_df
        .groupby(["Year","City","Latitude","Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # -------------------------------------------------------------------
    # 3) INTERACTIVE AREA CHART (Brush) + STACKED BAR + MAP
    # -------------------------------------------------------------------
    st.subheader("1) Interactive Medal Counts over Time (Brushing to Filter)")

    # Interval brush along x-axis
    year_brush = alt.selection_interval(encodings=["x"])

    # AREA CHART: total medals by year
    area_chart = (
        alt.Chart(total_medals_by_year)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("Year:O", title="Year", sort=all_years),
            y=alt.Y("TotalMedals:Q", title="Total Medals"),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("TotalMedals:Q")
            ]
        )
        .add_selection(year_brush)
        .properties(width=500, height=250)
    )

    # STACKED BAR: medal distribution (filtered by brush)
    distribution_chart = (
        alt.Chart(medal_distribution)
        .mark_bar()
        .encode(
            x=alt.X("Year:O", title="Year", sort=all_years),
            y=alt.Y("Count:Q", stack="normalize", title="Proportion of Medals"),
            color=alt.Color("Medal:N", legend=alt.Legend(title="Medal Type")),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Medal:N"),
                alt.Tooltip("Count:Q")
            ]
        )
        .transform_filter(year_brush)
        .properties(width=500, height=250)
    )

    col1, col2 = st.columns([1,1])
    with col1:
        st.altair_chart(area_chart, use_container_width=True)
    with col2:
        st.altair_chart(distribution_chart, use_container_width=True)

    # MAP (filtered by brush)
    st.subheader("2) Host City Map (Filtered by Brushed Years)")
    world_map = alt.topo_feature(data.world_110m.url, feature='countries')

    base_map = (
        alt.Chart(world_map)
        .mark_geoshape(fill="lightgray", stroke="white")
        .properties(width=700, height=400)
        .project("naturalEarth1")
    )

    city_points = (
        alt.Chart(city_summary)
        .mark_circle(color="red", opacity=0.6)
        .encode(
            longitude=alt.Longitude("Longitude:Q"),
            latitude=alt.Latitude("Latitude:Q"),
            size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0,1000])),
            tooltip=[
                alt.Tooltip("City:N"),
                alt.Tooltip("Year:O"),
                alt.Tooltip("CityMedals:Q")
            ]
        )
        .transform_filter(year_brush)
    )

    city_map = base_map + city_points
    st.altair_chart(city_map, use_container_width=True)

    # -------------------------------------------------------------------
    # 4) BUBBLE CHART (Year vs. Country) + SINGLE SELECTION → BREAKDOWN
    # -------------------------------------------------------------------
    st.subheader("3) Bubble Chart (Year vs. Country)")

    # Single selection (no name=..., no param references)
    single_select = alt.selection_single(fields=["Year","Country"], empty="none")

    # Bubble chart
    bubble_chart = (
        alt.Chart(medal_by_year_country)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", title="Year", sort=all_years),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", legend=alt.Legend(title="Medals"), scale=alt.Scale(range=[0,1000])),
            color=alt.Color("MedalsWon:Q", scale=alt.Scale(scheme="blues"), legend=None),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Country:N"),
                alt.Tooltip("MedalsWon:Q")
            ]
        )
        .add_selection(single_select)
        .properties(width=700, height=400)
    )

    st.write("**Click a bubble to see that (year, country)'s medal breakdown.**")
    st.altair_chart(bubble_chart, use_container_width=True)

    # Breakdown bar chart
    st.subheader("4) Medal Breakdown for Selected Bubble")

    breakdown_chart = (
        alt.Chart(breakdown_src)
        .mark_bar()
        .encode(
            x=alt.X("Medal:N", title="Medal", sort=["Gold","Silver","Bronze"]),
            y=alt.Y("NumMedals:Q", title="Number of Medals"),
            color=alt.Color("Medal:N", legend=None),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Country:N"),
                alt.Tooltip("Medal:N"),
                alt.Tooltip("NumMedals:Q")
            ]
        )
        .transform_filter(single_select)
        .properties(width=300, height=300)
    )

    st.altair_chart(breakdown_chart, use_container_width=False)

    # -------------------------------------------------------------------
    # 5) DATA TABLE
    # -------------------------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.write("Raw data after applying the filters:")
        st.dataframe(filtered_df)

    st.markdown("---")
    st.markdown(
        "**Tips:**\n"
        "1. **Brush** across the area chart to select a range of years → updates the stacked bar & map.\n"
        "2. **Click** a bubble in the bubble chart to filter the breakdown bar.\n"
        "3. If 'Unrecognized signal name' errors persist, try:\n"
        "   ```bash\n"
        "   pip install --upgrade altair==4.2.2\n"
        "   # or\n"
        "   pip install --upgrade altair==5.0.1\n"
        "   ```"
    )

if __name__ == "__main__":
    main()
