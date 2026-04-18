import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.ui import display_aggrid
from utils.helpers import apply_time_filter

def render_searcher(df, global_start, global_end, global_time_filter, global_period, year_min, year_max):
    st.header("Music Search / Filter")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        track_input = st.text_input("Track contains")
        artist_input = st.text_input("Artist contains")
    
    with col2:
        album_input = st.text_input("Album contains")
    
    with col3:
        duration_range = st.slider(
            "Duration (seconds)",
            min_value=0,
            max_value=int(df["duration"].max()) if not df.empty else 600,
            value=(0, int(df["duration"].max()) if not df.empty else 600)
        )
    
    year_filter = st.slider(
        "Release year",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
    )

    df_search = df.copy()
    
    if track_input:
        df_search = df_search[df_search["track"].str.contains(track_input, case=False, na=False)]
    if artist_input:
        df_search = df_search[df_search["artist"].str.contains(artist_input, case=False, na=False)]
    if album_input:
        df_search = df_search[df_search["album"].str.contains(album_input, case=False, na=False)]
    
    df_search = df_search[
        (df_search["duration"].between(duration_range[0], duration_range[1])) &
        (df_search["year_release"].between(year_filter[0], year_filter[1]))
    ]

    if not df_search.empty:
        summary_search = (
            df_search.groupby(["track","artist","album"])
            .agg(
                Plays=("track", "count"),
                Minutes=("duration", lambda x: round(x.sum()/60, 2)),
                Year=("year_release", "first"),
                Duration=("duration", "first")
            )
            .reset_index()
            .sort_values("Minutes", ascending=False)
        )
    else:
        summary_search = pd.DataFrame(columns=["track","artist","album","Plays","Minutes","Year","Duration"])

    display_aggrid(summary_search, container_id="search_tab_grid")

    st.header("Artist diversity per period (Shannon index)")
    df_div = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_div = apply_time_filter(df_div, global_time_filter)
    if df_div.empty:
        st.info("No data")
    else:
        temp = df_div.copy()
        if global_period == "week":
            temp["Period"] = temp["datetime"].dt.to_period("W").apply(lambda r: r.start_time.date())
        elif global_period == "day":
            temp["Period"] = temp["datetime"].dt.date
        elif global_period == "month":
            temp["Period"] = temp["datetime"].dt.to_period("M").apply(lambda r: r.start_time.date())
        elif global_period == "year":
            temp["Period"] = temp["datetime"].dt.to_period("Y").apply(lambda r: r.start_time.date())
        
        counts = temp.groupby(["Period","artist"]).size()
        prop = counts.groupby(level=0).apply(lambda s: s / s.sum())
        shannon = prop.groupby(level=0).apply(lambda s: -(s * np.log(s)).sum())
        sh_df = shannon.reset_index(name="Shannon")
        
        try:
            sh_df["PeriodDt"] = pd.to_datetime(sh_df["Period"])
            sh_df = sh_df.sort_values("PeriodDt")
        except Exception:
            pass
        
        fig = px.line(sh_df, x="Period", y="Shannon", title="Artist diversity (Shannon index)")
        st.plotly_chart(fig, use_container_width=True)
