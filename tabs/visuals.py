import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.helpers import apply_time_filter, apply_top_n_others, get_genre_group

from utils.localization import get_text

def render_visuals(df, df_genre, global_start, global_end, global_time_filter, 
                   n_decades, n_genres, n_artists, n_albums, n_tracks, use_others, lang="en"):
    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 3.5rem;'>{get_text('tabs.galaxy', lang)} 🪐</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #b3b3b3;'>{get_text('visuals.subtitle', lang)}</h4>", unsafe_allow_html=True)
    st.write("---")

    # Filter data
    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter).copy()
    
    df_gen = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gen = apply_time_filter(df_gen, global_time_filter).copy()

    if df_filtered.empty or df_gen.empty:
        st.info("Not enough data to generate visual insights for this period.")
        return

    # --- 1. SUNBURST CHART (Decade -> Genre -> Artist) ---
    st.markdown("### 🪐 Musical Galaxy (Sunburst Chart)")
    st.markdown("Customize the hierarchy and order of the rings. Click on any ring to zoom in.")

    # 1. Ring selection and order — 4 selectboxes, one per position
    options_map = {
        "Decade": "decade",
        "Genre": "genre_single",
        "Artist": "artist",
        "Album": "album_clean",
        "Track": "track",
        "(none)": None,
    }
    labels = list(options_map.keys())

    st.markdown("**🔧 Configure the rings** (outer → inner):")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        r1 = st.selectbox("🔵 Ring 1", labels, index=0, key="ring1")
    with col2:
        r2 = st.selectbox("🟢 Ring 2", labels, index=1, key="ring2")
    with col3:
        r3 = st.selectbox("🟡 Ring 3", labels, index=2, key="ring3")
    with col4:
        r4 = st.selectbox("🔴 Ring 4", labels, index=3, key="ring4")
    with col5:
        r5 = st.selectbox("🟣 Ring 5", labels, index=4, key="ring5")

    # Build path ignoring "(ninguno)" and duplicates
    seen = set()
    sun_path = []
    for r in [r1, r2, r3, r4, r5]:
        col_val = options_map[r]
        if col_val and col_val not in seen:
            sun_path.append(col_val)
            seen.add(col_val)

    if not sun_path:
        sun_path = ["decade", "genre_single", "artist"]
    
    # We need a clean dataframe based on the selected path
    df_sun = df_gen.dropna(subset=sun_path)
    
    # Apply filters based on the selected path
    others_labels = {
        "decade": "Other Decades",
        "genre_single": "Other Genres",
        "artist": "Other Artists",
        "album_clean": "Other Albums",
        "track": "Other Tracks"
    }
    limits_map = {
        "decade": n_decades,
        "genre_single": n_genres,
        "artist": n_artists,
        "album_clean": n_albums,
        "track": n_tracks
    }

    for col in sun_path:
        df_sun = apply_top_n_others(
            df_sun, col, limits_map[col], 
            use_others=use_others, 
            others_label=others_labels[col]
        )
    
    sun_data = df_sun.groupby(sun_path)["duration"].sum().reset_index()
    sun_data["minutes"] = sun_data["duration"] / 60.0

    # Color is based on the outermost ring (first element of path)
    color_col = sun_path[0] if sun_path else None

    if not sun_data.empty:
        fig_sun = px.sunburst(
            sun_data, 
            path=sun_path, 
            values='minutes',
            color=color_col,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_sun.update_layout(
            margin=dict(t=10, l=10, r=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=700
        )
        fig_sun.update_traces(
            hovertemplate="<b>%{label}</b><br>Duration: %{value:.0f} mins<br>%{percentParent:.1%} of parent"
        )
        st.plotly_chart(fig_sun, use_container_width=True)
    else:
        st.warning("Not enough grouped data for the Sunburst chart.")

    st.write("<br><hr>", unsafe_allow_html=True)

    # --- 2. STREAMGRAPH (Genre Evolution) ---
    st.markdown("### 🌊 Genre Flow (Streamgraph)")
    st.markdown("Observe the waves of your top genres flowing over time.")
    
    # Group by month and top genres
    group_genres = st.checkbox("Group related genres (e.g. Hard Rock -> Rock)", value=False)
    
    df_stream = df_gen.copy()
    if group_genres:
        df_stream["genre_single"] = df_stream["genre_single"].apply(get_genre_group)
    
    df_stream = apply_top_n_others(df_stream, "genre_single", n_genres, use_others=use_others, others_label="Other Genres")
    
    df_stream["month"] = df_stream["datetime"].dt.to_period("M").dt.to_timestamp()
    stream_data = df_stream.groupby(["month", "genre_single"])["duration"].sum().reset_index()
    stream_data["minutes"] = stream_data["duration"] / 60.0

    if not stream_data.empty:
        # Create a Streamgraph (Stacked Area with spline interpolation)
        fig_stream = px.area(
            stream_data, 
            x="month", 
            y="minutes", 
            color="genre_single",
            line_group="genre_single",
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"month": "Timeline", "minutes": "Minutes Listened", "genre_single": "Genre"}
        )
        # Make the lines smooth
        fig_stream.update_traces(line=dict(shape='spline', smoothing=1.3), mode='lines', stackgroup='one')
        fig_stream.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
            height=500
        )
        st.plotly_chart(fig_stream, use_container_width=True)
    else:
        st.warning("Not enough monthly data for the Streamgraph.")

    st.write("<br><hr>", unsafe_allow_html=True)

    # --- 3. TREEMAP (Artist/Genre Mosaic) ---
    st.markdown("### 🧱 The Artist Mosaic (Treemap)")
    st.markdown("A nested view showing your most listened artists, grouped by their primary genre.")
    
    # We want a single dominant genre per artist for the treemap to avoid duplicates
    artist_durations = df_filtered.groupby("artist")["duration"].sum().reset_index()
    # Apply artist limit
    top_artist_names = artist_durations.nlargest(n_artists, "duration")["artist"]
    
    if not top_artist_names.empty:
        # If use_others is True, we keep everyone but label them "Other Artists"
        # However, for Treemap, showing everyone might be too much.
        # Let's respect the limit and only show "Others" if enabled.
        df_tree_base = df_filtered.copy()
        if use_others:
            df_tree_base.loc[~df_tree_base["artist"].isin(top_artist_names), "artist"] = "Other Artists"
        else:
            df_tree_base = df_tree_base[df_tree_base["artist"].isin(top_artist_names)]
        
        # Find dominant genre for each artist (including "Other Artists")
        artist_dominant_genre = df_gen[df_gen["artist"].isin(df_tree_base["artist"].unique())] \
            .groupby(["artist", "genre_single"])["duration"].sum() \
            .reset_index() \
            .sort_values("duration", ascending=False) \
            .drop_duplicates(subset=["artist"], keep="first")
        
        # Now get data at the artist-album-track level
        tree_data = df_tree_base.groupby(["artist", "album_clean", "track"])["duration"].sum().reset_index()
        
        # Apply album limit per artist or globally? 
        # Usually globally is easier to manage with the existing tool.
        tree_data = apply_top_n_others(tree_data, "album_clean", n_albums, use_others=use_others, others_label="Other Albums")
        
        # Merge the dominant genre back in
        tree_data = tree_data.merge(artist_dominant_genre[["artist", "genre_single"]], on="artist", how="left")
        tree_data["genre_single"] = tree_data["genre_single"].fillna("Unknown")
        tree_data["minutes"] = tree_data["duration"] / 60.0
        
        # Filter out very small entries to keep the map clean and performance high
        tree_data = tree_data[tree_data["minutes"] > 1]
        
        fig_tree = px.treemap(
            tree_data,
            path=["genre_single", "artist", "album_clean", "track"],
            values="minutes",
            color="genre_single",
            color_discrete_sequence=px.colors.qualitative.Vivid,
            maxdepth=4 # Ensure it tries to show all levels (Genre -> Artist -> Album -> Track)
        )
        fig_tree.update_traces(
            root_color="rgba(0,0,0,0)",
            marker=dict(line=dict(width=1, color="#121212")),
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>Duration: %{value:.1f} mins"
        )
        fig_tree.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=800 # Increased height to allow more space for album boxes
        )
        st.plotly_chart(fig_tree, use_container_width=True)
