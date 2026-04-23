import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import apply_time_filter, LOCAL_TZ
from utils.localization import get_text

def render_home(df, df_genre, global_start, global_end, global_time_filter, lang="en"):
    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 4rem; margin-bottom: 0;'>{get_text('home.title', lang)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #b3b3b3; margin-top: 0;'>{get_text('home.subtitle', lang)}</h4>", unsafe_allow_html=True)
    st.write("---")

    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter).copy()

    if df_filtered.empty:
        st.info("Welcome! Select a date range with data in the sidebar to get started.")
        return

    # --- Quick Stats Cards ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_mins = df_filtered["duration"].sum() / 60.0
    total_plays = len(df_filtered)
    unique_artists = df_filtered["artist"].nunique()
    
    with col1:
        st.metric(get_text("home.total_time", lang), f"{total_mins:.0f} min")
    with col2:
        st.metric(get_text("home.tracks_heard", lang), f"{total_plays:}")
    with col3:
        st.metric(get_text("home.unique_artists", lang), f"{unique_artists:,}")
    with col4:
        top_artist = df_filtered["artist"].mode()[0] if not df_filtered.empty else "-"
        st.metric(get_text("home.top_artist", lang), top_artist)

    st.write("<br>", unsafe_allow_html=True)

    # --- Feature Rows ---
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.markdown(f"### 🕒 {get_text('home.recent_activity', lang)}")
        last_5 = df_filtered.sort_values("datetime", ascending=False).head(5)
        last_5["Time"] = last_5["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%H:%M")
        last_5_display = last_5[["track", "artist", "Time"]].rename(columns={"track": "Track", "artist": "Artist"})
        st.dataframe(last_5_display, hide_index=True, use_container_width=True)

    with row1_col2:
        st.markdown(f"### 🌟 {get_text('home.vibe_check', lang)}")
        if not df_genre.empty:
            df_gen_filtered = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
            if not df_gen_filtered.empty:
                top_genre = df_gen_filtered["genre_single"].mode()[0]
                st.markdown(f"""
                <div style="background-color: #1e2a3e; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #FF4B4B;">
                    <h2 style="margin: 0; color: #FF4B4B;">{top_genre}</h2>
                    <p style="color: #b3b3b3; margin-top: 10px;">{get_text('home.vibe_subtitle', lang)}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("Not enough genre data.")
        else:
            st.write("Loading vibes...")

    st.write("<br>", unsafe_allow_html=True)

    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.markdown(f"### 📊 {get_text('home.daily_dist', lang)}")
        df_filtered["hour"] = df_filtered["datetime"].dt.hour
        hour_counts = df_filtered.groupby("hour").size().reset_index(name="Plays")
        fig_hour = px.bar(hour_counts, x="hour", y="Plays", color="Plays", color_continuous_scale="Reds")
        fig_hour.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_hour, use_container_width=True)

    with row2_col2:
        st.markdown(f"### 📅 {get_text('home.most_active_day', lang)}")
        df_filtered["date"] = df_filtered["datetime"].dt.date
        top_day = df_filtered["date"].value_counts().idxmax()
        top_day_plays = df_filtered["date"].value_counts().max()
        st.markdown(f"""
        <div style="background-color: #1e2a3e; padding: 20px; border-radius: 15px; text-align: center;">
            <h4 style="margin: 0; color: white;">{top_day.strftime('%d %B, %Y')}</h4>
            <h2 style="margin: 10px 0; color: #FF4B4B;">{top_day_plays} plays</h2>
            <p style="color: #b3b3b3; margin: 0;">{get_text('home.fire_day', lang)}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown(f"<p style='text-align: center; color: #555;'>{get_text('home.made_with', lang)}</p>", unsafe_allow_html=True)
