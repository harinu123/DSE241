# import streamlit as st
# import pandas as pd
# import altair as alt
# from vega_datasets import data  # For a simple world map background

# @st.cache_data
# def load_data():
#     # Load the JSON data (put olympics.json in the same folder)
#     df = pd.read_json("olympics.json")
#     return df

# def main():
#     # Set the page config
#     st.set_page_config(page_title="Winter Olympics Explorer", layout="wide")
#     st.title("Winter Olympics Medal Explorer (1924 – 2006)")

#     # -----------------------------------------------------
#     # 1) Load data & create sidebar filters
#     # -----------------------------------------------------
#     df = load_data()

#     st.sidebar.header("1) Data Filters")

#     all_years = sorted(df["Year"].unique())
#     # Year range slider
#     min_year, max_year = st.sidebar.select_slider(
#         "Select Year Range:",
#         options=all_years,
#         value=(min(all_years), max(all_years))
#     )

#     # Sports
#     all_sports = sorted(df["Sport"].unique())
#     selected_sports = st.sidebar.multiselect(
#         "Select Sports:",
#         options=all_sports,
#         default=all_sports
#     )

#     # Countries
#     all_countries = sorted(df["Country"].unique())
#     selected_countries = st.sidebar.multiselect(
#         "Select Countries:",
#         options=all_countries,
#         default=all_countries
#     )

#     # Genders
#     all_genders = ["M", "W", "X"]
#     selected_genders = st.sidebar.multiselect(
#         "Select Genders:",
#         options=all_genders,
#         default=all_genders
#     )

#     # Filter in Python (no Altair signals)
#     df_filtered = df[
#         (df["Year"] >= min_year)
#         & (df["Year"] <= max_year)
#         & (df["Sport"].isin(selected_sports))
#         & (df["Country"].isin(selected_countries))
#         & (df["Gender"].isin(selected_genders))
#     ]

#     st.sidebar.markdown(f"**Records after filtering:** {len(df_filtered)}")

#     # -----------------------------------------------------
#     # 2) AGGREGATIONS FOR CHARTS
#     # -----------------------------------------------------
#     # A) Area Chart: total medals by year
#     total_by_year = (
#         df_filtered
#         .groupby("Year")
#         .size()
#         .reset_index(name="TotalMedals")
#     )

#     # B) Stacked Bar: medal distribution by year & medal type
#     medal_distribution = (
#         df_filtered
#         .groupby(["Year","Medal"])
#         .size()
#         .reset_index(name="Count")
#     )

#     # C) Bubble Chart: (Year vs Country), sized by # of medals
#     year_country_medals = (
#         df_filtered
#         .groupby(["Year","Country"])
#         .size()
#         .reset_index(name="MedalsWon")
#     )

#     # D) Host City Summaries
#     city_summary = (
#         df_filtered
#         .groupby(["Year","City","Latitude","Longitude"])
#         .size()
#         .reset_index(name="CityMedals")
#     )

#     # E) Medal Breakdown – but we won't do an in-chart selection.  
#     #    Instead, the user picks a single (Year, Country) in the sidebar.
#     breakdown_full = (
#         df_filtered
#         .groupby(["Year","Country","Medal"])
#         .size()
#         .reset_index(name="NumMedals")
#     )

#     # -----------------------------------------------------
#     # 3) Layout: Area Chart & Stacked Bar
#     # -----------------------------------------------------
#     st.subheader("2) Total Medals Over Time (Area Chart)")

#     # AREA CHART
#     area_chart = (
#         alt.Chart(total_by_year)
#         .mark_area(opacity=0.6)
#         .encode(
#             x=alt.X("Year:O", sort=all_years, title="Year"),
#             y=alt.Y("TotalMedals:Q", title="Total Medals"),
#             tooltip=[
#                 alt.Tooltip("Year:O"),
#                 alt.Tooltip("TotalMedals:Q")
#             ]
#         )
#         .properties(width=600, height=300)
#     )
#     st.altair_chart(area_chart, use_container_width=True)

#     st.subheader("3) Medal Distribution by Year (Stacked Bar)")
#     stacked_bar = (
#         alt.Chart(medal_distribution)
#         .mark_bar()
#         .encode(
#             x=alt.X("Year:O", sort=all_years, title="Year"),
#             y=alt.Y("Count:Q", stack="normalize", title="Proportion of Medals"),
#             color=alt.Color("Medal:N", legend=alt.Legend(title="Medal")),
#             tooltip=[
#                 alt.Tooltip("Year:O"),
#                 alt.Tooltip("Medal:N"),
#                 alt.Tooltip("Count:Q")
#             ]
#         )
#         .properties(width=600, height=300)
#     )
#     st.altair_chart(stacked_bar, use_container_width=True)

#     # -----------------------------------------------------
#     # 4) HOST CITY MAP
#     # -----------------------------------------------------
#     st.subheader("4) Host City Map")

#     # We'll just plot all filtered host cities. (No brushing)
#     world = alt.topo_feature(data.world_110m.url, feature="countries")
#     base_map = (
#         alt.Chart(world)
#         .mark_geoshape(fill="lightgray", stroke="white")
#         .properties(width=700, height=400)
#         .project("naturalEarth1")
#     )

#     city_points = (
#         alt.Chart(city_summary)
#         .mark_circle(color="red", opacity=0.6)
#         .encode(
#             longitude=alt.Longitude("Longitude:Q"),
#             latitude=alt.Latitude("Latitude:Q"),
#             size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0,1000])),
#             tooltip=[
#                 alt.Tooltip("City:N"),
#                 alt.Tooltip("Year:O"),
#                 alt.Tooltip("CityMedals:Q")
#             ]
#         )
#     )
#     city_map = base_map + city_points
#     st.altair_chart(city_map, use_container_width=True)

#     # -----------------------------------------------------
#     # 5) BUBBLE CHART (Year vs Country)
#     # -----------------------------------------------------
#     st.subheader("5) Bubble Chart of (Year vs. Country)")

#     bubble_chart = (
#         alt.Chart(year_country_medals)
#         .mark_circle()
#         .encode(
#             x=alt.X("Year:O", sort=all_years, title="Year"),
#             y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
#             size=alt.Size("MedalsWon:Q", scale=alt.Scale(range=[0,1000])),
#             color=alt.Color("MedalsWon:Q", scale=alt.Scale(scheme="blues"), legend=None),
#             tooltip=[
#                 alt.Tooltip("Year:O"),
#                 alt.Tooltip("Country:N"),
#                 alt.Tooltip("MedalsWon:Q")
#             ]
#         )
#         .properties(width=700, height=400)
#     )
#     st.altair_chart(bubble_chart, use_container_width=True)

#     # -----------------------------------------------------
#     # 6) Medal Breakdown (Year + Country from Sidebar)
#     # -----------------------------------------------------
#     # Instead of an Altair-based single_select, let the user pick from a dropdown.
#     st.subheader("6) Medal Breakdown for a Selected (Year, Country)")
#     col_a, col_b = st.columns(2)

#     with col_a:
#         # Year selection
#         possible_years = sorted(df_filtered["Year"].unique())
#         selected_breakdown_year = st.selectbox(
#             "Select Year for Breakdown:",
#             options=possible_years
#         )

#     with col_b:
#         # Country selection
#         possible_countries = sorted(df_filtered["Country"].unique())
#         selected_breakdown_country = st.selectbox(
#             "Select Country for Breakdown:",
#             options=possible_countries
#         )

#     # Filter breakdown data
#     breakdown_filtered = breakdown_full[
#         (breakdown_full["Year"] == selected_breakdown_year) &
#         (breakdown_full["Country"] == selected_breakdown_country)
#     ]

#     breakdown_chart = (
#         alt.Chart(breakdown_filtered)
#         .mark_bar()
#         .encode(
#             x=alt.X("Medal:N", sort=["Gold","Silver","Bronze"]),
#             y=alt.Y("NumMedals:Q"),
#             color=alt.Color("Medal:N", legend=None),
#             tooltip=[
#                 alt.Tooltip("Year:O"),
#                 alt.Tooltip("Country:N"),
#                 alt.Tooltip("Medal:N"),
#                 alt.Tooltip("NumMedals:Q")
#             ]
#         )
#         .properties(width=300, height=300)
#     )

#     st.altair_chart(breakdown_chart, use_container_width=False)

#     # -----------------------------------------------------
#     # 7) Data Table
#     # -----------------------------------------------------
#     with st.expander("View Filtered Data Table"):
#         st.dataframe(df_filtered)

#     st.markdown("---")
#     # st.markdown(
        
#     # )

# if __name__ == "__main__":
#     main()
import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data  # For a simple world map background

# Use st.cache_data for caching
@st.cache_data
def load_data():
    # Load the JSON data (put olympics.json in the same folder)
    df = pd.read_json("olympics.json")
    return df

def main():
    # Set the page config
    st.set_page_config(page_title="Winter Olympics Explorer", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006)")

    # -----------------------------------------------------
    # 1) Load data & create sidebar filters
    # -----------------------------------------------------
    df = load_data()

    st.sidebar.header("1) Data Filters")

    all_years = sorted(df["Year"].unique())
    # Year range slider
    min_year, max_year = st.sidebar.select_slider(
        "Select Year Range:",
        options=all_years,
        value=(min(all_years), max(all_years))
    )

    # Sports
    all_sports = sorted(df["Sport"].unique())
    selected_sports = st.sidebar.multiselect(
        "Select Sports:",
        options=all_sports,
        default=all_sports
    )

    # Countries
    all_countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries:",
        options=all_countries,
        default=all_countries
    )

    # Genders
    all_genders = ["M", "W", "X"]
    selected_genders = st.sidebar.multiselect(
        "Select Genders:",
        options=all_genders,
        default=all_genders
    )

    # Filter in Python (no Altair signals)
    df_filtered = df[
        (df["Year"] >= min_year)
        & (df["Year"] <= max_year)
        & (df["Sport"].isin(selected_sports))
        & (df["Country"].isin(selected_countries))
        & (df["Gender"].isin(selected_genders))
    ]

    st.sidebar.markdown(f"**Records after filtering:** {len(df_filtered)}")

    # -----------------------------------------------------
    # 2) AGGREGATIONS FOR CHARTS
    # -----------------------------------------------------
    # A) Area Chart: total medals by year
    total_by_year = (
        df_filtered
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
    )

    # B) Stacked Bar: medal distribution by year & medal type
    medal_distribution = (
        df_filtered
        .groupby(["Year","Medal"])
        .size()
        .reset_index(name="Count")
    )

    # C) Bubble Chart: (Year vs Country), sized by # of medals
    year_country_medals = (
        df_filtered
        .groupby(["Year","Country"])
        .size()
        .reset_index(name="MedalsWon")
    )

    # D) Host City Summaries
    city_summary = (
        df_filtered
        .groupby(["Year","City","Latitude","Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # E) Medal Breakdown
    breakdown_full = (
        df_filtered
        .groupby(["Year","Country","Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    # -----------------------------------------------------
    # 3) Layout: Area Chart & Stacked Bar
    # -----------------------------------------------------
    st.subheader("2) Total Medals Over Time (Area Chart)")

    # AREA CHART with Zoom & Pan
    zoom = alt.selection_interval(bind='scales', encodings=['x'])

    area_chart = (
        alt.Chart(total_by_year)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("TotalMedals:Q", title="Total Medals"),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("TotalMedals:Q")
            ]
        )
        .add_selection(
            zoom
        )
        .properties(width=600, height=300)
    )
    st.altair_chart(area_chart.interactive(), use_container_width=True)

    st.subheader("3) Medal Distribution by Year (Stacked Bar)")

    # Stacked Bar with Selection
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
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("Count:Q", stack="normalize", title="Proportion of Medals"),
            color=alt.Color("Medal:N", legend=alt.Legend(title="Medal")),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Medal:N"),
                alt.Tooltip("Count:Q")
            ]
        )
        .add_selection(
            selection
        )
        .transform_filter(
            selection
        )
        .properties(width=600, height=300)
    )
    st.altair_chart(stacked_bar, use_container_width=True)

    # -----------------------------------------------------
    # 4) HOST CITY MAP
    # -----------------------------------------------------
    st.subheader("4) Host City Map")

    # Interactive Host City Map with Tooltip
    world = alt.topo_feature(data.world_110m.url, feature="countries")
    base_map = (
        alt.Chart(world)
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
            size=alt.Size("CityMedals:Q", scale=alt.Scale(range=[0, 1000])),
            tooltip=[
                alt.Tooltip("City:N"),
                alt.Tooltip("Year:O"),
                alt.Tooltip("CityMedals:Q")
            ]
        )
        .interactive()  # Enable pan and zoom on the map
    )
    city_map = base_map + city_points
    st.altair_chart(city_map, use_container_width=True)

    # -----------------------------------------------------
    # 5) BUBBLE CHART (Year vs Country)
    # -----------------------------------------------------
    st.subheader("5) Bubble Chart of (Year vs. Country)")

    # Interactive Bubble Chart with Hover
    bubble_chart = (
        alt.Chart(year_country_medals)
        .mark_circle()
        .encode(
            x=alt.X("Year:O", sort=all_years, title="Year"),
            y=alt.Y("Country:N", sort=alt.SortField("Country", order="ascending")),
            size=alt.Size("MedalsWon:Q", scale=alt.Scale(range=[0, 1000])),
            color=alt.Color("MedalsWon:Q", scale=alt.Scale(scheme="blues"), legend=None),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Country:N"),
                alt.Tooltip("MedalsWon:Q")
            ]
        )
        .properties(width=700, height=400)
        .interactive()  # Enable zoom and pan
    )
    st.altair_chart(bubble_chart, use_container_width=True)

    # -----------------------------------------------------
    # 6) Medal Breakdown (Year + Country from Sidebar)
    # -----------------------------------------------------
    st.subheader("6) Medal Breakdown for a Selected (Year, Country)")
    col_a, col_b = st.columns(2)

    with col_a:
        # Year selection
        possible_years = sorted(df_filtered["Year"].unique())
        selected_breakdown_year = st.selectbox(
            "Select Year for Breakdown:",
            options=possible_years
        )

    with col_b:
        # Country selection
        possible_countries = sorted(df_filtered["Country"].unique())
        selected_breakdown_country = st.selectbox(
            "Select Country for Breakdown:",
            options=possible_countries
        )

    # Filter breakdown data
    breakdown_filtered = breakdown_full[
        (breakdown_full["Year"] == selected_breakdown_year) &
        (breakdown_full["Country"] == selected_breakdown_country)
    ]

    breakdown_chart = (
        alt.Chart(breakdown_filtered)
        .mark_bar()
        .encode(
            x=alt.X("Medal:N", sort=["Gold","Silver","Bronze"], title="Medal Type"),
            y=alt.Y("NumMedals:Q", title="Number of Medals"),
            color=alt.Color("Medal:N", scale=alt.Scale(domain=["Gold", "Silver", "Bronze"],
                                                      range=["gold", "silver", "brown"]),
                            legend=None),
            tooltip=[
                alt.Tooltip("Year:O"),
                alt.Tooltip("Country:N"),
                alt.Tooltip("Medal:N"),
                alt.Tooltip("NumMedals:Q")
            ]
        )
        .properties(width=300, height=300)
    )

    st.altair_chart(breakdown_chart, use_container_width=False)

    # -----------------------------------------------------
    # 7) Data Table
    # -----------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.dataframe(df_filtered)

    st.markdown("---")
    # You can add additional sections or information here

if __name__ == "__main__":
    main()
