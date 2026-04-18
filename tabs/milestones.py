import streamlit as st
import pandas as pd
from utils.helpers import apply_time_filter

def render_milestones(df, global_start, global_end, global_time_filter):
    st.markdown("<h1 style='text-align: center; color: #1DB954; font-size: 4rem; margin-bottom: 0;'>Your Milestones</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #b3b3b3; margin-top: 0;'>A chronological journey of your listening achievements</h4>", unsafe_allow_html=True)
    st.write("---")

    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter).copy()

    if df_filtered.empty:
        st.info("No data available to calculate milestones.")
        return

    # Sort chronologically
    df_sorted = df_filtered.sort_values("datetime").reset_index(drop=True)
    
    milestones = []

    # 1. Plays Milestones
    play_thresholds = [100, 500, 1000, 5000, 10000, 25000, 50000, 100000]
    for threshold in play_thresholds:
        if len(df_sorted) >= threshold:
            row = df_sorted.iloc[threshold - 1]
            milestones.append({
                "date": row["datetime"],
                "type": "Plays",
                "title": f"🎉 Reached {threshold:,} Total Plays",
                "desc": f"The milestone song was **{row['track']}** by **{row['artist']}**.",
                "color": "#1DB954",
                "icon": "🎧"
            })

    # 2. Hours Milestones
    df_sorted["cumulative_minutes"] = df_sorted["duration"].fillna(0).cumsum() / 60.0
    hour_thresholds = [10, 50, 100, 250, 500, 1000, 2000, 5000]
    for h in hour_thresholds:
        idx = df_sorted[df_sorted["cumulative_minutes"] >= (h * 60)].first_valid_index()
        if idx is not None:
            row = df_sorted.loc[idx]
            milestones.append({
                "date": row["datetime"],
                "type": "Hours",
                "title": f"⏳ Reached {h:,} Hours of Listening",
                "desc": f"You crossed this epic mark while listening to **{row['track']}** by **{row['artist']}**.",
                "color": "#FF4B4B",
                "icon": "⏱️"
            })

    # 3. Top Artist Milestones
    top_artist = df_sorted.groupby("artist")["duration"].sum().idxmax()
    df_artist = df_sorted[df_sorted["artist"] == top_artist].reset_index(drop=True)
    
    artist_thresholds = [50, 100, 250, 500, 1000, 5000]
    for threshold in artist_thresholds:
        if len(df_artist) >= threshold:
            row = df_artist.iloc[threshold - 1]
            milestones.append({
                "date": row["datetime"],
                "type": "Artist",
                "title": f"🎸 {threshold:,} Plays for {top_artist}",
                "desc": f"You reached this level of fandom listening to **{row['track']}**.",
                "color": "#FFD700",
                "icon": "⭐"
            })

    if not milestones:
        st.info("Not enough listening history yet to hit major milestones!")
        return

    # Sort milestones chronologically
    milestones = sorted(milestones, key=lambda x: x["date"])

    st.markdown("### 🏆 Timeline")
    for m in milestones:
        date_str = m["date"].strftime("%B %d, %Y - %H:%M")
        
        card_html = f"""
        <div style="border-left: 4px solid {m['color']}; padding-left: 20px; margin-bottom: 30px; background-color: #1e2a3e; padding: 15px 15px 15px 20px; border-radius: 0 10px 10px 0;">
            <p style="color: #b3b3b3; margin: 0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">{date_str}</p>
            <h3 style="margin: 5px 0; color: white;">{m['icon']} {m['title']}</h3>
            <p style="margin: 0; font-size: 1.1rem; color: #e0e0e0;">{m['desc']}</p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
