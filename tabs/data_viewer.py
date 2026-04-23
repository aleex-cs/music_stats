import streamlit as st
import pandas as pd
from utils.helpers import (
    apply_time_filter, get_decade, longest_consecutive_block_details, 
    longest_consecutive_block_minutes, summarize, add_share_columns, 
    split_genres, LOCAL_TZ
)

from utils.localization import get_text

def render_data_viewer(df, df_genre, global_start, global_end, global_time_filter, global_rows_to_show, lang="en"):
    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 3.5rem;'>{get_text('tabs.rankings', lang)} 🏆</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #b3b3b3;'>{get_text('data_viewer.subtitle', lang)}</h4>", unsafe_allow_html=True)
    st.write("---")
    df_fd = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_fd = apply_time_filter(df_fd, global_time_filter).copy()

    df_fd["track"] = df_fd["track"].astype(str).str.title().str.strip()
    df_fd["artist"] = df_fd["artist"].astype(str).str.title().str.strip()
    if "album" in df_fd.columns:
        df_fd["album"] = df_fd["album"].astype(str).str.title().str.strip()

    df_fd["decade"] = df_fd["year_release"].apply(get_decade)
    df_fd_dec = df_fd[df_fd["decade"].notna()]

    if not df_fd.empty:
        data_start = df_fd["datetime"].min()
        data_end = df_fd["datetime"].max()
        effective_start = max(global_start, data_start)
        effective_end = min(global_end, data_end)
        effective_days = max(1, (effective_end - effective_start).days + 1)
    else:
        effective_days = 1

    total_minutes_fd = df_fd["duration"].sum() / 60 if not df_fd.empty else 0.0
    plays_per_day = round(len(df_fd) / effective_days, 2)
    minutes_per_day = round(total_minutes_fd / effective_days, 2)

    # Tracks
    st.markdown("### Tracks")
    n_unique_tracks = df_fd["track"].nunique()
    avg_minutes_per_track = round(total_minutes_fd / n_unique_tracks, 2) if n_unique_tracks else 0.0

    c1, c2, c4, c3 = st.columns(4)
    c1.metric("Unique tracks", n_unique_tracks)
    c2.metric("Minutes per track", f"{avg_minutes_per_track:.2f} min")
    c3.metric("Plays per day", plays_per_day)
    c4.metric("Minutes per day", f"{minutes_per_day:.2f} min")

    top_track_val, top_track_size, first_play, last_play = longest_consecutive_block_details(df_fd, "track")
    c1, c2, c3 = st.columns(3)
    if top_track_val:
        c1.metric("Longest track repeat streak", f"{top_track_size} plays of {top_track_val}", help=f"{top_track_size} plays of {top_track_val}")
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        c1.metric("Longest track repeat streak", "-")
        c2.metric("First play of the streak", "-")
        c3.metric("Last play of the streak", "-")

    mt1, mt2, mt3 = st.columns(3)
    track_val_m, track_minutes, first_m, last_m = longest_consecutive_block_minutes(df_fd, "track")
    if track_val_m:
        mt1.metric("Longest track minutes streak", f"{track_minutes:.2f} min of {track_val_m}")
        mt2.metric("First play of the minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'))
        mt3.metric("Last play of the minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        mt1.metric("Longest track minutes streak", "-")
        mt2.metric("First play of the minutes streak", "-")
        mt3.metric("Last play of the minutes streak", "-")

    tracks_summary = summarize(df_fd, "track").rename(columns={"track": "Track"})
    tracks_summary = add_share_columns(tracks_summary)

    track_artist = (
        df_fd.groupby(["track", "artist"])
        .size().reset_index(name="count")
        .sort_values(["track", "count"], ascending=[True, False])
        .drop_duplicates("track", keep="first")[["track", "artist"]]
    )

    track_first_listen = df_fd.groupby("track")["datetime"].min().reset_index()
    track_first_listen["First Listen"] = track_first_listen["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%d/%m/%Y %H:%M:%S")

    tracks_summary = (
        tracks_summary
        .merge(track_artist, left_on="Track", right_on="track", how="left")
        .drop(columns=["track"])
        .merge(track_first_listen[["track", "First Listen"]], left_on="Track", right_on="track", how="left")
        .drop(columns=["track"])
    )
    tracks_summary["Artist"] = tracks_summary["artist"].fillna("Unknown")
    tracks_summary = tracks_summary[["Track", "Artist", "First Listen", "Minutes", "Minutes%", "Plays", "Plays%"]].head(global_rows_to_show)
    st.dataframe(tracks_summary, hide_index=True, use_container_width=True,height=(len(tracks_summary) + 1) * 35 + 3)

    # Artists
    st.markdown("### Artists")
    n_unique_artists = df_fd["artist"].nunique()
    avg_minutes_per_artist = round(total_minutes_fd / n_unique_artists, 2) if n_unique_artists else 0.0

    c1, c2, c4, c3 = st.columns(4)
    c1.metric("Unique artists", n_unique_artists)
    c2.metric("Minutes per artist", f"{avg_minutes_per_artist:.2f} min")
    c3.metric("Plays per day", plays_per_day)
    c4.metric("Minutes per day", f"{minutes_per_day:.2f} min")

    top_artist_val, top_artist_size, first_play, last_play = longest_consecutive_block_details(df_fd, "artist")
    c1, c2, c3 = st.columns(3)
    if top_artist_val:
        c1.metric("Longest artist repeat streak", f"{top_artist_size} plays of {top_artist_val}")
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        c1.metric("Longest artist repeat streak", "-")
        c2.metric("First play of the streak", "-")
        c3.metric("Last play of the streak", "-")

    ma1, ma2, ma3 = st.columns(3)
    artist_val_m, artist_minutes, first_m, last_m = longest_consecutive_block_minutes(df_fd, "artist")
    if artist_val_m:
        ma1.metric("Longest artist minutes streak", f"{artist_minutes:.2f} min of {artist_val_m}")
        ma2.metric("First play of the minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'))
        ma3.metric("Last play of the minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        ma1.metric("Longest artist minutes streak", "-")
        ma2.metric("First play of the minutes streak", "-")
        ma3.metric("Last play of the minutes streak", "-")

    artists_summary = summarize(df_fd, "artist").rename(columns={"artist": "Artist"})
    artists_summary = add_share_columns(artists_summary)
    _df_afl = df.copy()
    _df_afl["artist"] = _df_afl["artist"].astype(str).str.title().str.strip()
    artist_first_listen = _df_afl.groupby("artist")["datetime"].min().reset_index()
    artist_first_listen["First Listen"] = artist_first_listen["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%d/%m/%Y %H:%M:%S")
    artists_summary = artists_summary.merge(artist_first_listen, left_on="Artist", right_on="artist", how="left")
    artists_summary = artists_summary[["Artist", "First Listen", "Minutes", "Minutes%", "Plays", "Plays%"]].head(global_rows_to_show)
    st.dataframe(artists_summary, hide_index=True, use_container_width=True, height=(len(artists_summary) + 1) * 35 + 3)

    # Albums
    st.markdown("### Albums")
    n_unique_albums = df_fd["album_clean"].nunique() 
    avg_minutes_per_album = round(total_minutes_fd / n_unique_albums, 2) if n_unique_albums else 0.0

    c1, c2, c4, c3 = st.columns(4)
    c1.metric("Unique albums", n_unique_albums)
    c2.metric("Minutes per album", f"{avg_minutes_per_album:.2f} min")
    c3.metric("Plays per day", plays_per_day)
    c4.metric("Minutes per day", f"{minutes_per_day:.2f} min")

    top_album_val, top_album_size, first_play, last_play = longest_consecutive_block_details(df_fd, "album_clean")
    c1, c2, c3 = st.columns(3)
    if top_album_val:
        c1.metric("Longest album repeat streak", f"{top_album_size} plays of {top_album_val}")
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'))

    mal1, mal2, mal3 = st.columns(3)
    album_val_m, album_minutes, first_m, last_m = longest_consecutive_block_minutes(df_fd, "album_clean")
    if album_val_m:
        mal1.metric("Longest album minutes streak", f"{album_minutes:.2f} min of {album_val_m}")
        mal2.metric("First play of the minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'))
        mal3.metric("Last play of the minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'))

    albums_summary = summarize(df_fd, "album_clean").rename(columns={"album_clean": "Album"})
    albums_summary = add_share_columns(albums_summary)
    
    album_artist = (
        df_fd.groupby(["album_clean", "artist"]).size().reset_index(name="count")
        .sort_values(["album_clean", "count"], ascending=[True, False])
        .drop_duplicates("album_clean")[["album_clean", "artist"]]
    )
    
    album_first_listen = df_fd.groupby("album_clean")["datetime"].min().reset_index()
    album_first_listen["First Listen"] = album_first_listen["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%d/%m/%Y %H:%M:%S")
    
    albums_summary = (
        albums_summary
        .merge(album_artist, left_on="Album", right_on="album_clean", how="left")
        .merge(album_first_listen, on="album_clean", how="left")
    )
    
    albums_summary.rename(columns={"artist": "Artist"}, inplace=True)
    albums_summary = albums_summary[["Album", "Artist", "First Listen", "Minutes", "Minutes%", "Plays", "Plays%"]].head(global_rows_to_show)
    st.dataframe(albums_summary, hide_index=True, use_container_width=True, height=(len(albums_summary) + 1) * 35 + 3)

    # Genres
    st.markdown("### Genres")
    df_gf = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gf = apply_time_filter(df_gf, global_time_filter).copy()

    n_unique_genres = df_gf["genre_single"].nunique()
    minutes_by_genre = (df_gf.groupby("genre_single")["duration"].sum() / 60).sort_values(ascending=False)
    avg_minutes_per_genre = float(minutes_by_genre.mean()) if n_unique_genres else 0.0

    t1, t2, t4, t3 = st.columns(4)
    t1.metric("Unique genres", n_unique_genres)
    t2.metric("Minutes per genre", f"{avg_minutes_per_genre:.2f} min")
    t3.metric("Plays per day", plays_per_day)
    t4.metric("Minutes per day", f"{minutes_per_day:.2f} min")

    df_seq = df_fd.sort_values("datetime").copy()
    df_seq["primary_genre"] = df_seq["genre"].apply(lambda x: split_genres(x)[0] if split_genres(x) else None)
    df_seq["prev_genre"] = df_seq["primary_genre"].shift()
    df_seq["new_block"] = df_seq["primary_genre"] != df_seq["prev_genre"]
    df_seq["block"] = df_seq["new_block"].cumsum()

    if df_seq["primary_genre"].notna().any():
        repeats = df_seq.groupby(["primary_genre", "block"]).size()
        top_repeats = repeats.groupby("primary_genre").max().sort_values(ascending=False)
        top_genre_streak = top_repeats.index[0]
        genre_plays = df_seq[df_seq["primary_genre"] == top_genre_streak].sort_values("datetime")
        genre_plays["diff"] = genre_plays["datetime"].diff().dt.total_seconds().fillna(0)
        genre_plays["streak_id"] = (genre_plays["diff"] > 3600).cumsum()
        streak_lengths = genre_plays.groupby("streak_id").size()
        longest_streak_df = genre_plays[genre_plays["streak_id"] == streak_lengths.idxmax()]

        first_play = longest_streak_df["datetime"].min()
        last_play = longest_streak_df["datetime"].max()
        c1, c2, c3 = st.columns(3)
        c1.metric("Longest genre repeat streak", f"{top_repeats.iloc[0]} plays of {top_genre_streak}")
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        st.info("No hay géneros válidos para calcular rachas en el rango/turno seleccionado.")

    mg1, mg2, mg3 = st.columns(3)
    genre_val_m, genre_minutes, first_m, last_m = longest_consecutive_block_minutes(df_seq.rename(columns={"primary_genre":"genre_primary"}), "genre_primary")
    if genre_val_m:
        mg1.metric("Longest genre minutes streak", f"{genre_minutes:.2f} min of {genre_val_m}")
        mg2.metric("First play of the minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'))
        mg3.metric("Last play of the minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        mg1.metric("Longest genre minutes streak", "-")
        mg2.metric("First play of the minutes streak", "-")
        mg3.metric("Last play of the minutes streak", "-")

    if not df_gf.empty:
        genres_summary = (
            df_gf.groupby("genre_single")
            .agg(Minutes=("duration", lambda x: round(x.sum() / 60.0, 2)),
                 Plays=("genre_single", "count"))
            .sort_values("Minutes", ascending=False)
            .reset_index()
            .rename(columns={"genre_single": "Genre"})
        )
        total_minutes_g = genres_summary["Minutes"].sum()
        total_plays_g = genres_summary["Plays"].sum()
        genres_summary["Minutes%"] = (genres_summary["Minutes"] / total_minutes_g * 100) if total_minutes_g else 0.0
        genres_summary["Plays%"] = (genres_summary["Plays"] / total_plays_g * 100) if total_plays_g else 0.0
        genre_first_listen = df_genre.groupby("genre_single")["datetime"].min().reset_index()
        genre_first_listen["First Listen"] = genre_first_listen["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%d/%m/%Y %H:%M:%S")
        genres_summary = genres_summary.merge(genre_first_listen, left_on="Genre", right_on="genre_single", how="left")
        genres_summary = genres_summary[["Genre", "First Listen", "Minutes", "Minutes%", "Plays", "Plays%"]].head(global_rows_to_show)
        st.dataframe(genres_summary, hide_index=True, use_container_width=True, height=(len(genres_summary) + 1) * 35 + 3)
        
    else:
        st.write("No hay datos de géneros en el rango/turno seleccionado.")

    # Decades
    st.markdown("### Decades")
    n_unique_decades = df_fd_dec["decade"].nunique()
    avg_minutes_per_decade = round((df_fd_dec["duration"].sum() / 60) / n_unique_decades, 2) if n_unique_decades else 0.0

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Unique decades", n_unique_decades)
    d2.metric("Minutes per decade", f"{avg_minutes_per_decade:.2f} min")
    d3.metric("Plays per day", plays_per_day)
    d4.metric("Minutes per day", f"{minutes_per_day:.2f} min")

    top_dec_val, top_dec_size, first_play, last_play = longest_consecutive_block_details(df_fd_dec, "decade")
    c1, c2, c3 = st.columns(3)
    if top_dec_val:
        c1.metric("Longest decade repeat streak", f"{top_dec_size} plays of {top_dec_val}")
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        c1.metric("Longest decade repeat streak", "-")
        c2.metric("First play of the streak", "-")
        c3.metric("Last play of the streak", "-")

    dm1, dm2, dm3 = st.columns(3)
    dec_val_m, dec_minutes, first_m, last_m = longest_consecutive_block_minutes(df_fd_dec, "decade")
    if dec_val_m:
        dm1.metric("Longest decade minutes streak", f"{dec_minutes:.2f} min of {dec_val_m}")
        dm2.metric("First play of minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'))
        dm3.metric("Last play of minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        dm1.metric("Longest decade minutes streak", "-")
        dm2.metric("First play of minutes streak", "-")
        dm3.metric("Last play of minutes streak", "-")

    decades_summary = (
        df_fd_dec.groupby("decade")
        .agg(Minutes=("duration", lambda x: round(x.sum() / 60.0, 2)),
             Plays=("decade", "count"))
        .reset_index()
        .rename(columns={"decade": "Decade"})
    )
    total_m = decades_summary["Minutes"].sum()
    total_p = decades_summary["Plays"].sum()
    decades_summary["Minutes%"] = total_m and (decades_summary["Minutes"] / total_m * 100)
    decades_summary["Plays%"] = total_p and (decades_summary["Plays"] / total_p * 100)

    decade_first_listen = (
        df[df["year_release"].notna()]
        .assign(decade=df["year_release"].apply(get_decade))
        .groupby("decade")["datetime"].min()
        .reset_index()
    )
    decade_first_listen["First Listen"] = decade_first_listen["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%d/%m/%Y %H:%M:%S")
    decades_summary = decades_summary.merge(decade_first_listen, left_on="Decade", right_on="decade", how="left")
    decades_summary = decades_summary[["Decade", "First Listen", "Minutes", "Minutes%", "Plays", "Plays%"]].sort_values("Minutes", ascending=False).head(global_rows_to_show)
    st.dataframe(decades_summary, hide_index=True, use_container_width=True, height=(len(decades_summary) + 1) * 35 + 3)
