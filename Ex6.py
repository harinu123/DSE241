import streamlit as st
import pandas as pd
import altair as alt

def main():
    st.title("West Nile Virus in California - Corrected Weekly Chart")

    # Load data
    df = pd.read_csv("West_Nile_Virus_by_County.csv")

    # Ensure columns exist
    required_cols = {"Year", "Week_Reported", "County", "Positive_Cases"}
    if not required_cols.issubset(df.columns):
        st.error(f"Missing columns! Need at least: {required_cols}")
        return

    # Convert Week_Reported to numeric
    df["Week_Reported"] = pd.to_numeric(df["Week_Reported"], errors="coerce")

    # Sidebar: pick year
    years = sorted(df["Year"].unique())
    selected_year = st.sidebar.selectbox("Select Year", years)

    # Sidebar: pick counties (optional)
    all_counties = sorted(df["County"].unique())
    selected_counties = st.sidebar.multiselect("Select Counties", all_counties, default=all_counties[:5])

    # Filter data
    year_df = df[(df["Year"] == selected_year) & (df["County"].isin(selected_counties))]

    # Group by county + week to sum multiple rows
    weekly_agg = (
        year_df.groupby(["County", "Week_Reported"], as_index=False)["Positive_Cases"]
        .sum()
    )

    # Create line chart
    time_series = (
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
        .properties(width=700, height=400, title=f"Weekly Positive Cases by County ({selected_year})")
        .interactive()
    )

    st.altair_chart(time_series, use_container_width=True)

    # Show data table
    st.subheader(f"Data for {selected_year}")
    st.write(weekly_agg)

if __name__ == "__main__":
    main()
