import streamlit as st
import pandas as pd
from utils.helpers import apply_time_filter
from utils.localization import get_text

def render_milestones(df, df_genre, global_start, global_end, global_time_filter, lang="en"):
    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 4rem; margin-bottom: 0;'>{get_text('milestones.title', lang)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #b3b3b3; margin-top: 0;'>{get_text('milestones.subtitle', lang)}</h4>", unsafe_allow_html=True)
    st.write("---")

    # --- Filter UI ---
    st.markdown(f"### 🔍 {get_text('milestones.filter_type', lang)}")
    col1, col2 = st.columns(2)
    
    with col1:
        m_type = st.selectbox(
            "Type", 
            [
                get_text("milestones.global", lang), 
                get_text("milestones.artist", lang), 
                get_text("milestones.track", lang), 
                get_text("milestones.decade", lang)
            ]
        )
    
    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter).copy()

    if df_filtered.empty:
        st.info("No data available to calculate milestones.")
        return

    # Map localized type back to key
    type_map = {
        get_text("milestones.global", lang): "Global",
        get_text("milestones.artist", lang): "Artist",
        get_text("milestones.track", lang): "Track",
        get_text("milestones.decade", lang): "Decade"
    }
    selected_type = type_map[m_type]

    target_df = df_filtered.sort_values("datetime").reset_index(drop=True)
    milestones = []

    if selected_type == "Global":
        # 1. Total Plays Milestones
        play_thresholds = [100, 500, 1000, 5000, 10000, 25000, 50000, 100000]
        for threshold in play_thresholds:
            if len(target_df) >= threshold:
                row = target_df.iloc[threshold - 1]
                milestones.append({
                    "date": row["datetime"],
                    "title": f"{threshold:,} Total Plays",
                    "desc": f"The milestone song was **{row['track']}** by **{row['artist']}**.",
                    "color": "#1DB954",
                    "icon": "🎧"
                })

        # 2. Total Hours Milestones
        target_df["cumulative_minutes"] = target_df["duration"].fillna(0).cumsum() / 60.0
        hour_thresholds = [10, 50, 100, 250, 500, 1000, 2000, 5000]
        for h in hour_thresholds:
            idx = target_df[target_df["cumulative_minutes"] >= (h * 60)].first_valid_index()
            if idx is not None:
                row = target_df.loc[idx]
                milestones.append({
                    "date": row["datetime"],
                    "title": f"{h:,} Hours of Listening",
                    "desc": f"You crossed this mark with **{row['track']}** by **{row['artist']}**.",
                    "color": "#FF4B4B",
                    "icon": "⏱️"
                })

        # 3. Top 3 Milestones (Artists, Tracks, Albums, Genres, Decades)
        # Helper to add entity milestones
        def add_entity_milestones(df_base, entity_col, n=3, thresholds=[50, 100, 250, 500], icon="⭐", color="#FFD700", label=""):
            top_n = df_base[entity_col].value_counts().head(n).index
            for entity in top_n:
                df_ent = df_base[df_base[entity_col] == entity].sort_values("datetime").reset_index(drop=True)
                for t in thresholds:
                    if len(df_ent) >= t:
                        row = df_ent.iloc[t - 1]
                        milestones.append({
                            "date": row["datetime"],
                            "title": f"{t:,} {label} Plays: {entity}",
                            "desc": f"A major achievement for one of your top {label.lower()}s!",
                            "color": color,
                            "icon": icon
                        })

        # Top 3 Artists
        add_entity_milestones(target_df, "artist", n=3, thresholds=[50, 100, 250, 500, 1000], icon="🎸", color="#FFD700", label="Artist")
        # Top 3 Tracks
        add_entity_milestones(target_df, "track", n=3, thresholds=[10, 25, 50, 100], icon="🎵", color="#1DB954", label="Track")
        # Top 3 Albums
        add_entity_milestones(target_df, "album_clean", n=3, thresholds=[25, 50, 100, 250], icon="💿", color="#FF4B4B", label="Album")
        
        # Top 3 Genres (from df_genre)
        df_gen_filtered = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
        df_gen_filtered = apply_time_filter(df_gen_filtered, global_time_filter).sort_values("datetime")
        if not df_gen_filtered.empty:
            top_genres = df_gen_filtered["genre_single"].value_counts().head(3).index
            for gen in top_genres:
                df_g = df_gen_filtered[df_gen_filtered["genre_single"] == gen].reset_index(drop=True)
                for t in [100, 250, 500, 1000]:
                    if len(df_g) >= t:
                        row = df_g.iloc[t - 1]
                        milestones.append({
                            "date": row["datetime"],
                            "title": f"{t:,} Plays in {gen}",
                            "desc": f"Your ears love this genre!",
                            "color": "#9b59b6",
                            "icon": "🎷"
                        })
        
        # Top 3 Decades
        add_entity_milestones(target_df[target_df["decade"].notna()], "decade", n=3, thresholds=[100, 500, 1000, 2500], icon="🗓️", color="#3498db", label="Decade")

    elif selected_type == "Artist":
        with col2:
            artist_list = sorted(df_filtered["artist"].unique())
            selected_artist = st.selectbox(get_text("milestones.select_artist", lang), artist_list)
        
        df_artist = target_df[target_df["artist"] == selected_artist].reset_index(drop=True)
        thresholds = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
        for t in thresholds:
            if len(df_artist) >= t:
                row = df_artist.iloc[t - 1]
                milestones.append({
                    "date": row["datetime"],
                    "title": f"{t:,} Plays for {selected_artist}",
                    "desc": f"Milestone reached with **{row['track']}**.",
                    "color": "#FFD700",
                    "icon": "⭐"
                })

    elif selected_type == "Track":
        with col2:
            track_list = sorted(df_filtered["track"].unique())
            selected_track = st.selectbox(get_text("milestones.select_track", lang), track_list)
            
        df_track = target_df[target_df["track"] == selected_track].reset_index(drop=True)
        thresholds = [5, 10, 25, 50, 100, 250]
        for t in thresholds:
            if len(df_track) >= t:
                row = df_track.iloc[t - 1]
                milestones.append({
                    "date": row["datetime"],
                    "title": f"{t:,} Plays of {selected_track}",
                    "desc": f"Keep the rhythm going!",
                    "color": "#1DB954",
                    "icon": "🔥"
                })

    elif selected_type == "Decade":
        with col2:
            decade_list = sorted(df_filtered["decade"].dropna().unique())
            selected_decade = st.selectbox(get_text("milestones.select_decade", lang), decade_list)
            
        df_dec = target_df[target_df["decade"] == selected_decade].reset_index(drop=True)
        df_dec["cumulative_minutes"] = df_dec["duration"].fillna(0).cumsum() / 60.0
        hour_thresholds = [1, 5, 10, 25, 50, 100, 250]
        for h in hour_thresholds:
            idx = df_dec[df_dec["cumulative_minutes"] >= (h * 60)].first_valid_index()
            if idx is not None:
                row = df_dec.loc[idx]
                milestones.append({
                    "date": row["datetime"],
                    "title": f"{h:,} Hours in the {selected_decade}",
                    "desc": f"Time traveling with **{row['track']}**.",
                    "color": "#FF4B4B",
                    "icon": "⏳"
                })

    if not milestones:
        st.info(get_text("milestones.no_data", lang))
        return

    # Sort milestones chronologically
    milestones = sorted(milestones, key=lambda x: x["date"])

    st.markdown(f"### {get_text('milestones.timeline', lang)}")
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
