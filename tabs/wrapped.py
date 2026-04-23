import streamlit as st
import pandas as pd
from utils.helpers import apply_time_filter
from utils.api import get_album_cover, fetch_itunes_results, save_override, get_artist_image, fetch_deezer_artist

def cover_picker_ui(artist, album, key):
    with st.expander(f"✏️ Change image for {artist}"):
        if key == "artist":
            results = fetch_deezer_artist(artist, limit=10)
            query_key = f"artist_image - {artist}".strip().lower()
        else:
            query = f"{artist} {album}"
            results = fetch_itunes_results(query, limit=10)
            query_key = f"{artist} - {album}".strip().lower()
        
        if not results:
            st.warning("No alternative images found.")
            return
            
        cols = st.columns(5)
        for i, res in enumerate(results[:10]):
            col = cols[i % 5]
            with col:
                st.image(res["url"], use_container_width=True)
                st.caption(f"{res['album'][:25]}...")
                if st.button("Select", key=f"select_{key}_{artist}_{i}"):
                    save_override(query_key, res["url"])
                    st.rerun()

from utils.localization import get_text

def render_wrapped(df, df_genre, global_start, global_end, global_time_filter, lang="en"):
    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 4rem; font-weight: 800; margin-bottom: 0;'>{get_text('tabs.flashback', lang)} 🎁</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #b3b3b3; margin-top: 0;'>{get_text('wrapped.subtitle', lang)}</h4>", unsafe_allow_html=True)
    st.write("---")

    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter)

    if df_filtered.empty:
        st.info("No data available for this period.")
        return

    total_minutes = round(df_filtered["duration"].sum() / 60)
    total_plays = len(df_filtered)
    unique_artists = df_filtered["artist"].nunique()
    unique_tracks = df_filtered["track"].nunique()

    top_artist = df_filtered.groupby("artist")["duration"].sum().idxmax()
    top_artist_mins = round(df_filtered.groupby("artist")["duration"].sum().max() / 60)

    top_track_row = df_filtered.groupby(["track", "artist"])["duration"].sum().reset_index()
    top_track_row = top_track_row.loc[top_track_row["duration"].idxmax()]
    top_track = top_track_row["track"]
    top_track_artist = top_track_row["artist"]
    top_track_plays = df_filtered[df_filtered["track"] == top_track]["track"].count()

    top_album_row = df_filtered[df_filtered["album"].notna()].groupby(["album", "artist"])["duration"].sum().reset_index()
    if not top_album_row.empty:
        top_album_row = top_album_row.loc[top_album_row["duration"].idxmax()]
        top_album = top_album_row["album"]
        top_album_artist = top_album_row["artist"]
    else:
        top_album, top_album_artist = None, None

    col1, col2, col3, col4 = st.columns(4)
    
    def styled_metric(label, value):
        return f"""
        <div style="background-color: #1e2a3e; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
            <p style="color: #b3b3b3; font-size: 1.2rem; margin: 0;">{label}</p>
            <p style="color: #ffffff; font-size: 2.5rem; font-weight: bold; margin: 0;">{value}</p>
        </div>
        """

    col1.markdown(styled_metric("Total Minutes", f"{total_minutes:,}"), unsafe_allow_html=True)
    col2.markdown(styled_metric("Total Plays", f"{total_plays:,}"), unsafe_allow_html=True)
    col3.markdown(styled_metric("Different Artists", f"{unique_artists:,}"), unsafe_allow_html=True)
    col4.markdown(styled_metric("Different Tracks", f"{unique_tracks:,}"), unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)

    st.markdown("### 🏆 Top Artist")
    c1, c2 = st.columns([1, 2])
    artist_cover = get_artist_image(top_artist)
    
    with c1:
        if artist_cover:
            st.image(artist_cover, use_container_width=True)
        else:
            st.markdown("<div style='height:300px; background-color:#282828; display:flex; align-items:center; justify-content:center; border-radius:10px;'><h3 style='color: white;'>No Image</h3></div>", unsafe_allow_html=True)
        cover_picker_ui(top_artist, None, "artist")

    with c2:
        st.markdown(f"<h1 style='font-size: 4rem; margin-bottom: 0;'>{top_artist}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color: #1DB954; font-weight: 300;'>{top_artist_mins:,} minutes listened</h2>", unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🎵 Top Track")
        
        try:
            track_album = df_filtered[df_filtered["track"] == top_track]["album"].iloc[0]
        except:
            track_album = "Single"
            
        track_cover = get_album_cover(top_track_artist, track_album)
        if track_cover:
            st.image(track_cover, width=300)
            
        st.markdown(f"<h2>{top_track}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='color: #b3b3b3;'>by {top_track_artist}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #1DB954; font-weight: bold; font-size: 1.2rem;'>Played {top_track_plays} times</p>", unsafe_allow_html=True)
        cover_picker_ui(top_track_artist, track_album, "track")

    with c2:
        if top_album:
            st.markdown("### 💿 Top Album")
            album_cover = get_album_cover(top_album_artist, top_album)
            if album_cover:
                st.image(album_cover, width=300)
                
            st.markdown(f"<h2>{top_album}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='color: #b3b3b3;'>by {top_album_artist}</h4>", unsafe_allow_html=True)
            cover_picker_ui(top_album_artist, top_album, "album")

    st.write("<br><br><hr>", unsafe_allow_html=True)

    # --- MORE STATS ---
    st.markdown("### 🌟 More Statistics")
    m1, m2, m3 = st.columns(3)
    
    df_gf = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gf = apply_time_filter(df_gf, global_time_filter)
    top_genre_val = "-"
    if not df_gf.empty:
        top_genre_val = df_gf.groupby("genre_single")["duration"].sum().idxmax()
    m1.markdown(styled_metric("Top Genre", top_genre_val.title()), unsafe_allow_html=True)
    
    df_dec = df_filtered[df_filtered["decade"].notna()]
    top_decade_val = "-"
    if not df_dec.empty:
        top_decade_val = df_dec.groupby("decade")["duration"].sum().idxmax()
    m2.markdown(styled_metric("Top Decade", top_decade_val), unsafe_allow_html=True)
        
    first_listen = df.groupby("track")["datetime"].min().reset_index()
    new_tracks_count = first_listen[(first_listen["datetime"] >= global_start) & (first_listen["datetime"] <= global_end)].shape[0]
    m3.markdown(styled_metric("New Discoveries", f"{new_tracks_count:,}"), unsafe_allow_html=True)

    st.write("<br><hr>", unsafe_allow_html=True)

    # --- DOWNLOAD BUTTON ---
    html_content = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <title>Your Music Wrapped</title>
    <style>
    body {{ background-color: #121212; color: #ffffff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; text-align: center; padding: 40px; margin: 0; }}
    h1 {{ color: #1DB954; font-size: 4rem; margin-bottom: 5px; }}
    h4 {{ color: #b3b3b3; margin-top: 0; margin-bottom: 40px; }}
    .metrics-container {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 40px; }}
    .metric {{ background-color: #1e2a3e; padding: 20px; border-radius: 10px; width: 200px; border: 1px solid rgba(255,255,255,0.1); }}
    .metric p {{ margin: 0; }}
    .metric .val {{ font-size: 2.5rem; font-weight: bold; color: white; }}
    .metric .lbl {{ color: #b3b3b3; font-size: 1.1rem; }}
    .tops-container {{ display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; }}
    .top-card {{ background-color: #282828; padding: 30px; border-radius: 15px; width: 300px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    .top-card img {{ width: 100%; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 20px; }}
    .top-card h2 {{ margin: 0 0 10px 0; font-size: 2rem; }}
    .top-card h3 {{ color: #b3b3b3; margin: 0 0 15px 0; font-weight: normal; }}
    .top-card .tag {{ color: #1DB954; font-weight: bold; font-size: 1.2rem; }}
    .title-tag {{ text-transform: uppercase; letter-spacing: 2px; color: #b3b3b3; font-size: 0.9rem; margin-bottom: 15px; display: block; }}
    </style>
    </head>
    <body>
        <h1>Your Music Wrapped</h1>
        <h4>A summary of your listening habits</h4>
        
        <div class="metrics-container">
            <div class="metric"><p class="lbl">Total Minutes</p><p class="val">{total_minutes:,}</p></div>
            <div class="metric"><p class="lbl">Total Plays</p><p class="val">{total_plays:,}</p></div>
            <div class="metric"><p class="lbl">Different Artists</p><p class="val">{unique_artists:,}</p></div>
            <div class="metric"><p class="lbl">New Discoveries</p><p class="val">{new_tracks_count:,}</p></div>
        </div>
        
        <div class="tops-container">
            <div class="top-card">
                <span class="title-tag">Top Artist</span>
                <img src="{artist_cover or ''}" />
                <h2>{top_artist}</h2>
                <span class="tag">{top_artist_mins:,} mins</span>
            </div>
            
            <div class="top-card">
                <span class="title-tag">Top Track</span>
                <img src="{track_cover or ''}" />
                <h2>{top_track}</h2>
                <h3>by {top_track_artist}</h3>
                <span class="tag">Played {top_track_plays} times</span>
            </div>
            
            <div class="top-card">
                <span class="title-tag">Top Album</span>
                <img src="{album_cover or ''}" />
                <h2>{top_album or 'N/A'}</h2>
                <h3>by {top_album_artist or 'N/A'}</h3>
            </div>
        </div>
    </body>
    </html>
    """

    st.markdown("### 📥 Download your Wrapped")
    st.markdown("Guarda tu resumen visual como archivo web para verlo en cualquier momento o imprimirlo a PDF.")
    st.download_button(
        label="Download Wrapped (HTML)",
        data=html_content,
        file_name="my_music_wrapped.html",
        mime="text/html",
        use_container_width=True
    )
