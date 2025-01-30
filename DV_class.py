import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For the world map background

@st.cache_data
def load_data():
    # Load the JSON data
    df = pd.read_json("olympics.json")
    return df

def main():
    st.set_page_config(page_title="Winter Olympics Explorer", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006)")

    # -----------------------------------------------------
    # 1) Load data & create sidebar filters
    # -----------------------------------------------------
    df = load_data()

    st.sidebar.header("Filters")

    all_years = sorted(df["Year"].unique())
    min_year, max_year = st.sidebar.select_slider(
        "Select Year Range:",
        options=all_years,
        value=(min(all_years), max(all_years))
    )

    sports = sorted(df["Sport"].unique())
    selected_sports = st.sidebar.multiselect(
        "Select Sports:",
        options=sports,
        default=sports
    )

    countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries:",
        options=countries,
        default=countries
    )

    genders = ["M", "W", "X"]
    selected_genders = st.sidebar.multiselect(
        "Select Genders:",
        options=genders,
        default=genders
    )

    # Filter in Python (avoid param signals for these filters)
    df_filtered = df[
        (df["Year"] >= min_year)
        & (df["Year"] <= max_year)
        & (df["Sport"].isin(selected_sports))
        & (df["Country"].isin(selected_countries))
        & (df["Gender"].isin(selected_genders))
    ]

    st.sidebar.write(f"**Rows after filtering:** {len(df_filtered)}")

    # -----------------------------------------------------
    # 2) Aggregations
    # -----------------------------------------------------
    # (A) Area Chart: total medals by year
    total_by_year = (
        df_filtered
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    # (B) Stacked Bar: medal distribution by year & medal type
    distribution = (
        df_filtered
        .groupby(["Year","Medal"])
        .size()
        .reset_index(name="Count")
    )

    # (C) Host city summary
    city_summary = (
        df_filtered
        .groupby(["Year","City","Latitude","Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # (D) Year-Country medal counts (bubble chart)
    year_country = (
        df_filtered
        .groupby(["Year","Country"])
        .size()
        .reset_index(name="MedalsWon")
    )

    # (E) Breakdown by (Year, Country, Medal) for bar chart
    breakdown = (
        df_filtered
        .groupby(["Year","Country","Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    # -----------------------------------------------------
    # 3) AREA CHART (Interval Brush) + STACKED BAR + MAP
    # -----------------------------------------------------
    st.subheader("1) Total Medals Over Time (Brush the Year Range)")

    # Interval brush across the x-axis (Year)
    year_brush = alt.selection_interval(encodings=["x"])

    # Area chart
    area_chart = (
        alt.Chart(total_by_year)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("Year:O", sort=all_years),
            y=alt.Y("TotalMedals:Q"),
            # Keep tooltip minimal
            tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("TotalMedals:Q")]
        )
        .add_selection(year_brush)
        .properties(width=500, height=250)
    )

    # Stacked bar chart
    stacked_bar = (
        alt.Chart(distribution)
        .mark_bar()
        .encode(
            x=alt.X("Year:O", sort=all_years),
            y=alt.Y("Count:Q", stack="normalize"),
            color=alt.Color("Medal:N", legend=alt.Legend(title="Medal")),
            tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("Medal:N"), alt.Tooltip("Count:Q")]
        )
        .transform_filter(year_brush)
        .properties(width=500, height=250)
    )

    col1, col2 = st.columns([1,1])
    with col1:
        st.altair_chart(area_chart, use_container_width=True)
    with col2:
        st.altair_chart(stacked_bar, use_container_width=True)

    # Map of host cities filtered by the same brush
    st.subheader("2) Host City Map (Filtered by Brushed Years)")

    world = alt.topo_feature(data.world_110m.url, feature="countries")
    base_map = (
        alt.Chart(world)
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

    # -----------------------------------------------------
    # 4) BUBBLE CHART + SINGLE SELECTION → BREAKDOWN
    # -----------------------------------------------------
    st.subheader("3) Bubble Chart of (Year vs. Country)")

    # Single selection
    # We'll keep it simple: select by clicking on a circle
    bubble_select = alt.selection_single(fields=["Year","Country"], on="click", empty="none")

    bubble_chart = (
        alt.Chart(year_country)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", sort=all_years),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", scale=alt.Scale(range=[0, 1000])),
            color=alt.Color("MedalsWon:Q", scale=alt.Scale(scheme="blues"), legend=None),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Country:N"),
                alt.Tooltip("MedalsWon:Q")
            ]
        )
        .add_selection(bubble_select)
        .properties(width=700, height=400)
    )

    st.write("**Click a bubble to see that (Year, Country)'s medal breakdown.**")
    st.altair_chart(bubble_chart, use_container_width=True)

    # Breakdown bar chart (filtered by the single selection)
    st.subheader("4) Medal Breakdown for Selected Bubble")

    breakdown_chart = (
        alt.Chart(breakdown)
        .mark_bar()
        .encode(
            x=alt.X("Medal:N", sort=["Gold","Silver","Bronze"]),
            y=alt.Y("NumMedals:Q"),
            color=alt.Color("Medal:N", legend=None),
            tooltip=["Year","Country","Medal","NumMedals"]
        )
        .transform_filter(bubble_select)
        .properties(width=300, height=300)
    )

    st.altair_chart(breakdown_chart, use_container_width=False)

    # -----------------------------------------------------
    # 5) Data Table
    # -----------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.dataframe(df_filtered)

    st.markdown("---")
    st.markdown(
        "**Usage tips:**\n"
        "1. **Brush** across the *area chart* to filter a year range → Notice the stacked bar & map update.\n"
        "2. **Click** a bubble in the bubble chart to see a *medal breakdown* for that selection.\n"
        "3. If you still get 'unrecognized signal name' errors, try installing Altair 4.2.2 or 5.0.1.\n"
        "   ```bash\n"
        "   pip install --upgrade altair==4.2.2\n"
        "   # or\n"
        "   pip install --upgrade altair==5.0.1\n"
        "   ```"
    )

if __name__ == "__main__":
    main()
