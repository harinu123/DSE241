import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

def main():
    st.title("West Nile Virus in California: Map + Weekly Chart")

    # 1) Load data
    df = pd.read_csv("West_Nile_Virus_by_County.csv")

    # Ensure necessary columns exist
    required_cols = {"Year", "Week_Reported", "County", "id", "Positive_Cases"}
    if not required_cols.issubset(df.columns):
        st.error(f"Missing required columns: {required_cols}")
        st.stop()

    # Convert Week_Reported to numeric so Altair can properly sort
    df["Week_Reported"] = pd.to_numeric(df["Week_Reported"], errors="coerce")

    # 2) Sidebar: select year
    years = sorted(df["Year"].unique())
    selected_year = st.sidebar.selectbox("Select Year", years, index=0)

    # Filter data for the chosen year
    year_df = df[df["Year"] == selected_year]

    # 3) Choropleth Map: total Positive_Cases by county (for the selected year)
    county_agg = (
        year_df.groupby("id", as_index=False)["Positive_Cases"]
        .sum()
        .rename(columns={"Positive_Cases": "TotalCases"})
    )

    # Load US counties geometry from vega_datasets
    counties = alt.topo_feature(data.us_10m.url, "counties")

    # Build the Altair map for California only
    map_chart = (
        alt.Chart(counties)
        .mark_geoshape(stroke="white")
        .transform_calculate(
            # Each county's ID is stored in 'datum.id'.
            # We compute the state FIPS to filter out non-CA states.
            state_fips="floor(datum.id / 1000)"
        )
        .transform_filter(
            alt.datum.state_fips == 6  # 6 = California
        )
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(county_agg, key="id", fields=["TotalCases"])
        )
        .encode(
            color=alt.Color(
                "TotalCases:Q",
                title="Total Cases",
                scale=alt.Scale(scheme="reds")
            ),
            tooltip=[
                alt.Tooltip("TotalCases:Q", title="Total Cases"),
                # Optionally show the numeric 'id' on hover
                # alt.Tooltip("id:O", title="County FIPS")
            ]
        )
        .properties(
            width=600,
            height=400,
            title=f"Total WNV Cases by County ({selected_year})"
        )
        .project("albersUsa")
    )

    st.altair_chart(map_chart, use_container_width=True)

    # 4) Weekly Line Chart: Let user pick counties (optional)
    st.subheader("Weekly Positive Cases by County")

    all_counties = sorted(year_df["County"].unique())
    selected_counties = st.sidebar.multiselect(
        "Select Counties (for line chart)",
        all_counties,
        default=all_counties[:5]  # show a subset by default
    )

    # Filter to chosen counties
    line_df = year_df[year_df["County"].isin(selected_counties)]

    # Aggregate in case multiple rows exist for same county/week
    weekly_agg = (
        line_df.groupby(["County", "Week_Reported"], as_index=False)["Positive_Cases"]
        .sum()
    )

    # Build line chart with numeric x-axis
    line_chart = (
        alt.Chart(weekly_agg)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "Week_Reported:Q",
                title="Epidemiological Week",
                sort="ascending"
            ),
            y=alt.Y("Positive_Cases:Q", title="Positive Cases"),
            color="County:N",
            tooltip=["County:N", "Week_Reported:Q", "Positive_Cases:Q"]
        )
        .properties(width=700, height=400, title=f"Weekly Positive Cases ({selected_year})")
        .interactive()
    )

    st.altair_chart(line_chart, use_container_width=True)

    # 5) Display data table
    st.subheader(f"Data for {selected_year}")
    st.write(year_df)

if __name__ == "__main__":
    main()
