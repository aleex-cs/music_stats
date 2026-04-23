import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.helpers import apply_time_filter

from utils.localization import get_text

def render_searcher(df, df_genre, global_start, global_end, global_time_filter, global_period, year_min, year_max, lang="en"):
    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 3.5rem;'>{get_text('tabs.explorer', lang)} 🔍</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #b3b3b3;'>{get_text('searcher.subtitle', lang)}</h4>", unsafe_allow_html=True)
    st.write("---")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        track_input = st.text_input("Track contains")
        artist_input = st.text_input("Artist contains")
    
    with col2:
        album_input = st.text_input("Album contains")
        genre_input = st.text_input("Genre contains")
    
    with col3:
        duration_range = st.slider(
            "Duration (seconds)",
            min_value=0,
            max_value=int(df["duration"].max()) if not df.empty else 600,
            value=(0, int(df["duration"].max()) if not df.empty else 600)
        )
        specific_year = st.text_input("Specific Year (optional)")
    
    year_filter = st.slider(
        "Release year",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
    )

    df_search = df.copy()

    # Initial filters
    mask = (df_search["duration"].between(duration_range[0], duration_range[1]))
    
    if specific_year.isdigit():
        mask &= (df_search["year_release"] == int(specific_year))
    else:
        year_mask = df_search["year_release"].between(year_filter[0], year_filter[1]) | df_search["year_release"].isna()
        mask &= year_mask
    
    df_search = df_search[mask]


    if track_input:
        df_search = df_search[df_search["track"].str.contains(track_input, case=False, na=False)]
    if artist_input:
        df_search = df_search[df_search["artist"].str.contains(artist_input, case=False, na=False)]
    if album_input:
        df_search = df_search[df_search["album"].str.contains(album_input, case=False, na=False)]


    if genre_input:
        if genre_input.lower() == "unknown":
            known_datetimes = df_genre["datetime"].unique()
            matching_datetimes = df_genre[df_genre["genre_single"].str.contains("unknown", case=False, na=True)]["datetime"].unique()
            df_search = df_search[(df_search["datetime"].isin(matching_datetimes)) | (~df_search["datetime"].isin(known_datetimes))]
        else:
            matching_datetimes = df_genre[df_genre["genre_single"].str.contains(genre_input, case=False, na=False)]["datetime"]
            df_search = df_search[df_search["datetime"].isin(matching_datetimes)]

    if not df_search.empty:
        # Aggregate genres by datetime to avoid row duplication during merge
        df_genre_flat = df_genre.groupby("datetime")["genre_single"].apply(lambda x: sorted(set(x.dropna()))).reset_index()
        
        # Merge with genres
        df_search_with_genres = df_search.merge(
            df_genre_flat, 
            on="datetime", 
            how="left"
        )
        
        summary_search = (
            df_search_with_genres.groupby(["track","artist","album"])
            .agg(
                Plays=("track", "count"),
                Minutes=("duration", lambda x: round(x.sum()/60, 2)),
                Genres=("genre_single", lambda x: ", ".join(sorted(set([g for sublist in x.dropna() for g in sublist]))) if not x.dropna().empty else "-"),
                Year=("year_release", "first"),
                Duration=("duration", "first")
            )
            .reset_index()
            .sort_values("Minutes", ascending=False)
        )
    else:
        summary_search = pd.DataFrame(columns=["track","artist","album","Plays","Minutes","Genres","Year","Duration"])

    st.dataframe(summary_search, hide_index=True, use_container_width=True)

    st.markdown("### 🧬 Artist Diversity (Shannon Index)")
    with st.expander("What is Artist Diversity? (Shannon Index)"):
        st.markdown("""
        **Definition**: The Shannon Index measures the 'entropy' or variety of your listening habits. It considers both the number of different artists you listen to and how evenly your plays are distributed among them.
        
        **How it's calculated**: 
        $H' = - \sum p_i \ln(p_i)$
        *Where $p_i$ is the proportion of total plays that belong to artist $i$.*
        
        **How to interpret it**:
        - **Higher value**: You explore many different artists and don't concentrate your listening on just a few. Your taste is varied.
        - **Lower value**: Your listening is concentrated on a small set of artists (or just one, if the index is 0).
        """)
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
