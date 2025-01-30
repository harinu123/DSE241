import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events

@st.cache_data
def load_data():
    # Load the JSON data
    df = pd.read_json("olympics.json")
    return df

def main():
    st.set_page_config(page_title="Winter Olympics Explorer (Plotly)", layout="wide")
    st.title("Winter Olympics Medal Explorer (1924 – 2006) – Plotly Edition")

    # --------------------------------------------------
    # 1) LOAD DATA + SIDEBAR FILTERS
    # --------------------------------------------------
    df = load_data()

    st.sidebar.header("Filters")

    all_years = sorted(df["Year"].unique())
    year_min, year_max = st.sidebar.select_slider(
        "Year Range:",
        options=all_years,
        value=(min(all_years), max(all_years))
    )

    sports = sorted(df["Sport"].unique())
    selected_sports = st.sidebar.multiselect(
        "Sports:",
        options=sports,
        default=sports
    )

    countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Countries:",
        options=countries,
        default=countries
    )

    genders = ["M", "W", "X"]
    selected_genders = st.sidebar.multiselect(
        "Genders:",
        options=genders,
        default=genders
    )

    # Filter data in Python
    df_filtered = df[
        (df["Year"] >= year_min)
        & (df["Year"] <= year_max)
        & (df["Sport"].isin(selected_sports))
        & (df["Country"].isin(selected_countries))
        & (df["Gender"].isin(selected_genders))
    ]

    st.sidebar.write(f"Records after filtering: {len(df_filtered)}")

    # --------------------------------------------------
    # 2) AGGREGATIONS
    # --------------------------------------------------
    # (A) Total medals by year (for line chart)
    total_by_year = (
        df_filtered
        .groupby("Year")
        .size()
        .reset_index(name="TotalMedals")
        .sort_values("Year")
    )

    # (B) Medal distribution by year & medal type (for stacked bar)
    medal_distribution = (
        df_filtered
        .groupby(["Year","Medal"])
        .size()
        .reset_index(name="Count")
        .sort_values("Year")
    )

    # (C) City summary (for map)
    city_summary = (
        df_filtered
        .groupby(["Year","City","Latitude","Longitude"])
        .size()
        .reset_index(name="CityMedals")
    )

    # (D) Year vs. Country (bubble chart)
    year_country = (
        df_filtered
        .groupby(["Year","Country"])
        .size()
        .reset_index(name="MedalsWon")
        .sort_values(["Year","Country"])
    )

    # (E) Breakdown by (Year, Country, Medal)
    breakdown_df = (
        df_filtered
        .groupby(["Year","Country","Medal"])
        .size()
        .reset_index(name="NumMedals")
    )

    # --------------------------------------------------
    # 3) LINE CHART (TOTAL MEDALS) → SELECT YEAR
    # --------------------------------------------------
    st.subheader("1) Total Medals by Year (Click or Box/Lasso Select to Highlight Year)")

    # Create line chart with Plotly Express
    fig_line = px.line(
        total_by_year,
        x="Year",
        y="TotalMedals",
        markers=True,
        title="Total Medals Over Time"
    )

    # If we want box-select or lasso-select, set those as default drag modes
    fig_line.update_layout(dragmode="select")

    # Show chart with streamlit-plotly-events to capture selection
    selected_points_line = plotly_events(
        fig_line,
        click_event=True,
        select_event=True,
        override_height=500,
        override_width="100%"
    )
    # `selected_points_line` is a list of dicts with info about selected points

    # Extract the selected Year(s)
    if selected_points_line:
        # The user may have selected multiple points
        # Let's gather the distinct years
        selected_years = set()
        for pt in selected_points_line:
            # The x-value is the "Year"
            # Usually it's stored under 'x', but let's print to confirm
            # st.write(pt)  # debug
            if "x" in pt:
                selected_years.add(int(pt["x"]))
        # We'll refine the medal_distribution to just those year(s)
        st.info(f"**Selected Year(s)** from line chart: {sorted(selected_years)}")
    else:
        selected_years = set()  # if none selected, we show all years

    # --------------------------------------------------
    # 4) STACKED BAR: MEDAL DISTRIBUTION (per-year or selected year)
    # --------------------------------------------------
    st.subheader("2) Medal Distribution (Stacked Bar)")

    if selected_years:
        # Filter medal_distribution to only the selected year(s)
        df_bar = medal_distribution[medal_distribution["Year"].isin(selected_years)]
        bar_title = f"Medal Distribution for Selected Year(s): {sorted(selected_years)}"
    else:
        # Show all
        df_bar = medal_distribution
        bar_title = "Medal Distribution (All Filtered Years)"

    fig_bar = px.bar(
        df_bar,
        x="Year",
        y="Count",
        color="Medal",
        title=bar_title,
        labels={"Count":"Medal Count"},
    )
    fig_bar.update_layout(barmode="stack")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --------------------------------------------------
    # 5) HOST CITY MAP
    # --------------------------------------------------
    st.subheader("3) Host City Map")

    # We'll just plot the city_summary as a scatter_geo:
    if len(city_summary) == 0:
        st.write("No host city data for the current filters.")
    else:
        fig_map = px.scatter_geo(
            city_summary,
            lat="Latitude",
            lon="Longitude",
            size="CityMedals",
            hover_name="City",
            hover_data={"Year":True,"CityMedals":True,"Latitude":False,"Longitude":False},
            projection="natural earth",
            title="Host Cities (size ~ total medals awarded that year)"
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # --------------------------------------------------
    # 6) BUBBLE CHART (Year vs. Country) → SELECT (Year, Country) for Breakdown
    # --------------------------------------------------
    st.subheader("4) Bubble Chart: Year vs. Country (Click or Box Select)")

    fig_bubble = px.scatter(
        year_country,
        x="Year",
        y="Country",
        size="MedalsWon",
        size_max=40,
        color="MedalsWon",
        hover_data={"Year":True, "Country":True, "MedalsWon":True},
        title="Bubble Chart: (Year vs. Country, Size=Medals Won)"
    )
    fig_bubble.update_layout(dragmode="select")  # allow box/lasso

    selected_points_bubble = plotly_events(
        fig_bubble,
        click_event=True,
        select_event=True,
        override_height=600,
        override_width="100%"
    )

    # Now let's see if a (Year, Country) was selected
    # We can show a bar chart breakdown of medals for that pair
    selected_pairs = set()
    if selected_points_bubble:
        for pt in selected_points_bubble:
            # Usually year => 'x', country => 'y'
            sel_year = int(pt["x"]) if "x" in pt else None
            sel_country = pt["y"] if "y" in pt else None
            if sel_year and sel_country:
                selected_pairs.add((sel_year, sel_country))
        if selected_pairs:
            st.info(f"**Selected** (Year,Country) pairs: {selected_pairs}")

    # --------------------------------------------------
    # 7) MEDAL BREAKDOWN CHART
    # --------------------------------------------------
    st.subheader("5) Medal Breakdown for Selected (Year,Country) pairs")

    # Filter breakdown_df for those pairs (could be multiple)
    if selected_pairs:
        df_break = pd.DataFrame()
        for (yy, cc) in selected_pairs:
            temp = breakdown_df[
                (breakdown_df["Year"] == yy)
                & (breakdown_df["Country"] == cc)
            ]
            df_break = pd.concat([df_break, temp], ignore_index=True)
        if len(df_break) == 0:
            st.write("No data for the selected pairs.")
        else:
            fig_break = px.bar(
                df_break,
                x="Medal",
                y="NumMedals",
                color="Medal",
                facet_col="Country",   # separate columns if multiple countries selected
                facet_col_wrap=3,
                title="Medal Breakdown",
                labels={"NumMedals":"# of Medals","Medal":""},
            )
            st.plotly_chart(fig_break, use_container_width=True)
    else:
        st.write("Select one or more (Year, Country) in the bubble chart above to see the breakdown.")

    # --------------------------------------------------
    # 8) DATA TABLE
    # --------------------------------------------------
    with st.expander("View Filtered Data Table"):
        st.dataframe(df_filtered)

    st.markdown("---")
    st.markdown(
        "**Interactivity:**\n"
        "1. **Line Chart**: click or box-select across years → that filters the stacked bar to those selected years.\n"
        "2. **Bubble Chart**: click or box-select over points to pick (Year,Country). The breakdown bar shows details.\n"
        "3. The map & line chart do not do in-chart brushing that modifies other charts (besides the line → stacked bar), but this is a template you can expand.\n"
        "\n"
        "No hidden Altair param signals are used—Plotly events are captured via `streamlit-plotly-events`."
    )

if __name__ == "__main__":
    main()
