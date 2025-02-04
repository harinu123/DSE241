import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  

@st.cache_data
def load_data():
    df = pd.read_json("olympics.json")
    return df

def main():
    st.set_page_config(page_title="Winter Olympics Explorer", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006) – Color Corrected")

    df = load_data()

    st.sidebar.header("1) Data Filters")

    all_years = sorted(df["Year"].unique())
    min_year, max_year = st.sidebar.select_slider(
        "Select Year Range:",
        options=all_years,
        value=(min(all_years), max(all_years))
    )

    all_sports = sorted(df["Sport"].unique())
    selected_sports = st.sidebar.multiselect(
        "Select Sports:",
        options=all_sports,
        default=all_sports
    )

    all_countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries:",
        options=all_countries,
        default=all_countries
    )

    all_genders = ["M", "W", "X"]
    selected_genders = st.sidebar.multiselect(
        "Select Genders:",
        options=all_genders,
        default=all_genders
    )

    # Filter DataFrame in Python
    df_filtered = df[
        (df["Year"] >= min_year)
        & (df["Year"] <= max_year)
        & (df["Sport"].isin(selected_sports))
        & (df["Country"].isin(selected_countries))
        & (df["Gender"].isin(selected_genders))
    ]

    st.sidebar.markdown(f"**Records after filtering:** {len(df_filtered)}")

    # -----------------------------------------------------
    # Aggregations
    # -----------------------------------------------------
    total_by_year = (
        df_filtered
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    medal_distribution = (
        df_filtered
        .groupby(["Year","Medal"])
        .size()
        .reset_index(name="Count")
    )

    year_country_medals = (
        df_filtered
        .groupby(["Year","Country"])
        .size()
        .reset_index(name="MedalsWon")
    )

    city_summary = (
        df_filtered
        .groupby(["Year","City","Latitude","Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    breakdown_full = (
        df_filtered
        .groupby(["Year","Country","Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    st.subheader("2) Total Medals Over Time (Area Chart)")

    zoom = alt.selection_interval(bind='scales', encodings=['x'])

    area_chart = (
        alt.Chart(total_by_year)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("Year:O", title="Year", sort=sorted(total_by_year["Year"].unique())),
            y=alt.Y("TotalMedals:Q", title="Total Medals"),
            tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("TotalMedals:Q")]
        )
        .add_selection(zoom)
        .properties(width=600, height=300)
    )
    st.altair_chart(area_chart.interactive(), use_container_width=True)

    st.subheader("3) Medal Distribution by Year (Stacked Bar)")

    selection = alt.selection_single(
        fields=['Year'],
        empty='all',
        on='click',
        nearest=True
    )

    stacked_bar = (
        alt.Chart(medal_distribution)
        .mark_bar()
        .encode(
            x=alt.X("Year:O", sort=sorted(medal_distribution["Year"].unique()), title="Year"),
            y=alt.Y("Count:Q", stack="normalize", title="Proportion of Medals"),
            color=alt.Color(
                "Medal:N",
                legend=alt.Legend(title="Medal"),
                scale=alt.Scale(scheme="set2")
            ),
            tooltip=["Year:O", "Medal:N", "Count:Q"]
        )
        .add_selection(selection)
        .transform_filter(selection)
        .properties(width=600, height=300)
    )
    st.altair_chart(stacked_bar, use_container_width=True)


    st.subheader("4) Host City Map")

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
            longitude=alt.Longitude("Longitude:Q"),
            latitude=alt.Latitude("Latitude:Q"),
            size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0, 1000])),
            tooltip=["City:N", "Year:O", "CityMedals:Q"]
        )
        .interactive()
    )
    city_map = base_map + city_points
    st.altair_chart(city_map, use_container_width=True)

    st.subheader("5) Bubble Chart of (Year vs. Country)")

    bubble_chart = (
        alt.Chart(year_country_medals)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", sort=sorted(year_country_medals["Year"].unique()), title="Year"),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", scale=alt.Scale(range=[0,1000])),
            color=alt.Color(
                "MedalsWon:Q",
                legend=None,
                scale=alt.Scale(scheme="yellowgreenblue")
            ),
            tooltip=["Year:O", "Country:N", "MedalsWon:Q"]
        )
        .properties(width=700, height=400)
        .interactive()
    )
    st.altair_chart(bubble_chart, use_container_width=True)


    st.subheader("6) Medal Breakdown for a Selected (Year, Country)")

    col_a, col_b = st.columns(2)
    possible_years = sorted(df_filtered["Year"].unique())
    with col_a:
        selected_breakdown_year = st.selectbox(
            "Select Year for Breakdown:",
            options=possible_years
        )
    possible_countries = sorted(df_filtered["Country"].unique())
    with col_b:
        selected_breakdown_country = st.selectbox(
            "Select Country for Breakdown:",
            options=possible_countries
        )

    breakdown_filtered = breakdown_full[
        (breakdown_full["Year"] == selected_breakdown_year)
        & (breakdown_full["Country"] == selected_breakdown_country)
    ]


    medal_palette = ["#1b9e77", "#d95f02", "#7570b3"]

    breakdown_chart = (
        alt.Chart(breakdown_filtered)
        .mark_bar()
        .encode(
            x=alt.X("Medal:N", sort=["Gold","Silver","Bronze"], title="Medal Type"),
            y=alt.Y("NumMedals:Q", title="Number of Medals"),
            color=alt.Color(
                "Medal:N",
                scale=alt.Scale(
                    domain=["Gold","Silver","Bronze"],
                    range=medal_palette
                ),
                legend=None
            ),
            tooltip=["Year:O","Country:N","Medal:N","NumMedals:Q"]
        )
        .properties(width=300, height=300)
    )
    st.altair_chart(breakdown_chart, use_container_width=False)

    with st.expander("View Filtered Data Table"):
        st.dataframe(df_filtered)

    st.markdown("---")
    st.markdown(
        "**Note**: We use lowercase ColorBrewer scheme names (`'set2'`, `'yellowgreenblue'`, etc.) "
        "which are recognized by Altair v5. This ensures color scale validity and avoids schema "
        "validation errors."
    )

if __name__ == "__main__":
    main()
