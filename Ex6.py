import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

def main():
    st.title("West Nile Virus in California: Map + Weekly Chart")

    df = pd.read_csv("West_Nile_Virus_by_County.csv")

    required_cols = {"Year", "Week_Reported", "County", "id", "Positive_Cases"}
    if not required_cols.issubset(df.columns):
        st.error(f"Missing required columns: {required_cols}")
        st.stop()

    df["Week_Reported"] = pd.to_numeric(df["Week_Reported"], errors="coerce")

    years = sorted(df["Year"].unique())
    selected_year = st.sidebar.selectbox("Select Year", years, index=0)

    year_df = df[df["Year"] == selected_year]

    county_agg = (
        year_df.groupby("id", as_index=False)["Positive_Cases"]
        .sum()
        .rename(columns={"Positive_Cases": "TotalCases"})
    )

    counties = alt.topo_feature(data.us_10m.url, "counties")

    map_chart = (
        alt.Chart(counties)
        .mark_geoshape(stroke="white")
        .transform_calculate(
            state_fips="floor(datum.id / 1000)"
        )
        .transform_filter(
            alt.datum.state_fips == 6  
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

    st.subheader("Weekly Positive Cases by County")

    all_counties = sorted(year_df["County"].unique())
    selected_counties = st.sidebar.multiselect(
        "Select Counties (for line chart)",
        all_counties,
        default=all_counties[:5]  
    )

    line_df = year_df[year_df["County"].isin(selected_counties)]

    weekly_agg = (
        line_df.groupby(["County", "Week_Reported"], as_index=False)["Positive_Cases"]
        .sum()
    )

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

    st.subheader(f"Data for {selected_year}")
    st.write(year_df)

if __name__ == "__main__":
    main()
