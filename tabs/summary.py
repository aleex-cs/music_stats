import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from utils.helpers import (
    apply_time_filter, get_listening_summary, LOCAL_TZ, 
    longest_streak, format_first_listen_table
)

def render_summary(df, df_genre, global_start, global_end, global_time_filter, global_period, global_rows_to_show):
    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter)

    delta_days = max(1, (global_end - global_start).days + 1)
    prev_end = global_start - pd.Timedelta(seconds=1)
    prev_start = global_start - pd.Timedelta(days=delta_days)

    df_prev = df[(df["datetime"] >= prev_start) & (df["datetime"] <= prev_end)]
    df_prev = apply_time_filter(df_prev, global_time_filter)

    total_minutes = round(df_filtered["duration"].sum() / 60.0, 2)
    total_plays = len(df_filtered)

    prev_minutes = round(df_prev["duration"].sum() / 60.0, 2)
    prev_plays = len(df_prev)

    delta_minutes = round(total_minutes - prev_minutes, 2)
    delta_plays = total_plays - prev_plays

    st.markdown("### Resumen del Periodo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Minutes", f"{total_minutes} min", delta=f"{delta_minutes} min" if total_minutes > 0 or prev_minutes > 0 else None)
    col2.metric("Total Plays", total_plays, delta=delta_plays if total_plays > 0 or prev_plays > 0 else None)
    
    unique_artists = df_filtered["artist"].nunique()
    prev_unique_artists = df_prev["artist"].nunique()
    delta_artists = unique_artists - prev_unique_artists
    col3.metric("Unique Artists", unique_artists, delta=delta_artists if unique_artists > 0 or prev_unique_artists > 0 else None)

    st.markdown("---")

    summary_full = get_listening_summary(df_filtered, global_period)

    df_gf = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gf = apply_time_filter(df_gf, global_time_filter).copy()

    if global_period == "week":
        df_gf["Period"] = df_gf["datetime"].dt.to_period("W").apply(lambda r: r.start_time.tz_localize(LOCAL_TZ).date())
    elif global_period == "day":
        df_gf["Period"] = df_gf["datetime"].dt.tz_convert(LOCAL_TZ).dt.date
    elif global_period == "month":
        df_gf["Period"] = df_gf["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("M").apply(lambda r: r.start_time.date())
    elif global_period == "year":
        df_gf["Period"] = df_gf["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("Y").apply(lambda r: r.start_time.date())

    df_gf["Period"] = df_gf["Period"].astype(str)

    genre_per_period = (
        df_gf.groupby(["Period", "genre_single"])["duration"].sum().reset_index()
    )
    if not genre_per_period.empty:
        idx = genre_per_period.groupby("Period")["duration"].idxmax()
        top_genre_by_period = (
            genre_per_period.loc[idx, ["Period", "genre_single"]]
            .rename(columns={"genre_single": "Top Genre"})
        )
        summary_full = summary_full.drop(columns=["Top Genre"], errors="ignore") \
                                .merge(top_genre_by_period, on="Period", how="left")

    if not summary_full.empty:
        idx_max_minutes = summary_full["Minutes"].idxmax()
        idx_min_minutes = summary_full["Minutes"].idxmin()

        period_max_minutes_period = summary_full.loc[idx_max_minutes, "Period"]
        period_max_minutes_val = summary_full.loc[idx_max_minutes, "Minutes"]

        period_min_minutes_period = summary_full.loc[idx_min_minutes, "Period"]
        period_min_minutes_val = summary_full.loc[idx_min_minutes, "Minutes"]

        avg_minutes = round(summary_full["Minutes"].mean(), 2)

        idx_max_plays = summary_full["Plays"].idxmax()
        idx_min_plays = summary_full["Plays"].idxmin()

        period_max_plays_period = summary_full.loc[idx_max_plays, "Period"]
        period_max_plays_val = summary_full.loc[idx_max_plays, "Plays"]

        period_min_plays_period = summary_full.loc[idx_min_plays, "Period"]
        period_min_plays_val = summary_full.loc[idx_min_plays, "Plays"]

        avg_plays = round(summary_full["Plays"].mean(), 2)

        top_artist_series = summary_full.groupby("Top Artist").size()
        top_artist = top_artist_series.idxmax()
        top_artist_count = top_artist_series.max()

        top_track_series = summary_full.groupby("Top Track").size()
        top_track = top_track_series.idxmax()
        top_track_count = top_track_series.max()

        if "Top Album" in summary_full.columns:
            top_album_series = summary_full.groupby("Top Album").size()
            top_album = top_album_series.idxmax()
            top_album_count = top_album_series.max()
        else:
            top_album, top_album_count = None, 0
        
        if "Top Genre" in summary_full.columns:
            top_genre_series = summary_full.groupby("Top Genre").size()
            top_genre = top_genre_series.idxmax()
            top_genre_count = top_genre_series.max()
        else:
            top_genre, top_genre_count = None, 0

        top_decade_series = summary_full.groupby("Top Decade").size()
        top_decade = top_decade_series.idxmax()
        top_decade_count = top_decade_series.max()

        summary_sorted = summary_full.sort_values("Period")

        track_streak_val, track_streak_len = longest_streak(summary_sorted["Top Track"])
        artist_streak_val, artist_streak_len = longest_streak(summary_sorted["Top Artist"])
        album_streak_val, album_streak_len = longest_streak(summary_sorted["Top Album"]) if "Top Album" in summary_sorted.columns else (None, 0)
        genre_streak_val, genre_streak_len = longest_streak(summary_sorted["Top Genre"]) if "Top Genre" in summary_sorted.columns else (None, 0)
        decade_streak_val, decade_streak_len = longest_streak(summary_sorted["Top Decade"])

        first_track_listen = df.groupby("track")["datetime"].min().reset_index()
        new_tracks = first_track_listen[
            (first_track_listen["datetime"] >= global_start) &
            (first_track_listen["datetime"] <= global_end)
        ]

        first_artist_listen = df.groupby("artist")["datetime"].min().reset_index()
        new_artists = first_artist_listen[
            (first_artist_listen["datetime"] >= global_start) &
            (first_artist_listen["datetime"] <= global_end)
        ]

        first_album_listen = df.groupby("album_clean")["datetime"].min().reset_index()
        new_albums = first_album_listen[
            (first_album_listen["datetime"] >= global_start) &
            (first_album_listen["datetime"] <= global_end)
        ]

        first_genre_listen = df_genre.groupby("genre_single")["datetime"].min().reset_index()
        new_genres = first_genre_listen[
            (first_genre_listen["datetime"] >= global_start) &
            (first_genre_listen["datetime"] <= global_end)
        ]

        first_decade_listen = (
            df[df["decade"].notna()]
            .groupby("decade")["datetime"]
            .min()
            .reset_index(name="first_listen")
        )
        new_decades = first_decade_listen[
            (first_decade_listen["first_listen"] >= global_start) &
            (first_decade_listen["first_listen"] <= global_end)
        ]

        artist_counts = df_filtered["artist"].value_counts(normalize=True)
        diversity = 1 - (artist_counts**2).sum()

        r1, r2, r3 = st.columns(3)
        r1.metric("Period max minutes", f"{period_max_minutes_period} ({period_max_minutes_val} min)",
                  help=f"{period_max_minutes_period} ({period_max_minutes_val} min)")
        r2.metric(f"Average minutes per {global_period}", f"{avg_minutes} min")
        r3.metric("Period min minutes", f"{period_min_minutes_period} ({period_min_minutes_val} min)",
                   help=f"{period_min_minutes_period} ({period_min_minutes_val} min)")
        
        r1, r2, r3 = st.columns(3)
        r1.metric("Period max plays", f"{period_max_plays_period} ({period_max_plays_val} plays)",
                  help=f"{period_max_plays_period} ({period_max_plays_val} plays)")
        r2.metric(f"Average plays per {global_period}", f"{avg_plays}")
        r3.metric("Period min plays", f"{period_min_plays_period} ({period_min_plays_val} plays)",
                  help=f"{period_min_plays_period} ({period_min_plays_val} plays)")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Top Artist most repeated", f"{top_artist} ({top_artist_count})", help=f"{top_artist} ({top_artist_count})")
        c2.metric("Top Track most repeated",  f"{top_track} ({top_track_count})",   help=f"{top_track} ({top_track_count})")
        c3.metric("Top Album most repeated",  f"{top_album} ({top_album_count})",   help=f"{top_album} ({top_album_count})")
        c4.metric("Top Genre most repeated",  f"{top_genre} ({top_genre_count})" if pd.notna(top_genre) else "-",
                   help=f"{top_genre} ({top_genre_count})" if pd.notna(top_genre) else "-")
        c5.metric("Top Decade most repeated", f"{top_decade} ({top_decade_count})", help=f"{top_decade} ({top_decade_count})")

        r2, r1, r3, r4, r5 = st.columns(5)

        r2.metric("Longest Top Artist streak", f"{artist_streak_val} ({artist_streak_len})")
        r1.metric("Longest Top Track streak", f"{track_streak_val} ({track_streak_len})")
        r3.metric("Longest Top Album streak", f"{album_streak_val} ({album_streak_len})")
        r4.metric("Longest Top Genre streak", f"{genre_streak_val} ({genre_streak_len})")
        r5.metric("Longest Top Decade streak", f"{decade_streak_val} ({decade_streak_len})")

        r1, r2, r3, r4, r5 = st.columns(5)

        r1.metric("New artists discovered", len(new_artists))
        r2.metric("New tracks discovered", len(new_tracks))
        r3.metric("New albums discovered", len(new_albums))
        r4.metric("New genres discovered", len(new_genres))
        r5.metric("New decades discovered", len(new_decades))

        st.metric("Artist diversity index", round(diversity,3))
        
        summary_table = summary_full.sort_values("Period", ascending=False).head(global_rows_to_show)
        rows = len(summary_table)
        calculated_height = (rows + 1) * 35 + 3
        st.dataframe(summary_table,hide_index=True,use_container_width=True,height=calculated_height)
        
        st.markdown("## New Discoveries")

        if len(new_artists) > 0:
            artists_table = format_first_listen_table(new_artists, "artist").head(global_rows_to_show)
            st.markdown("### 🎤 New Artists")
            st.dataframe(artists_table,hide_index=True,use_container_width=True,height=(len(artists_table)+1)*35+3)
            
        if len(new_tracks) > 0:
            tracks_table = format_first_listen_table(new_tracks, "track").head(global_rows_to_show)
            st.markdown("### 🎵 New Tracks")
            st.dataframe(tracks_table, hide_index=True, use_container_width=True, height=(len(tracks_table)+1)*35+3)

        if len(new_albums) > 0:
            albums_table = format_first_listen_table(new_albums, "album_clean").head(global_rows_to_show)
            st.markdown("### 💿 New Albums")
            st.dataframe(albums_table, hide_index=True, use_container_width=True, height=(len(albums_table)+1)*35+3)

        if len(new_genres) > 0:
            genres_table = format_first_listen_table(new_genres, "genre_single").head(global_rows_to_show)
            st.markdown("### 🎼 New Genres")
            st.dataframe(genres_table, hide_index=True, use_container_width=True, height=(len(genres_table)+1)*35+3)

        if len(new_decades) > 0:
            decades_table = new_decades.copy()
            decades_table["first_listen"] = decades_table["first_listen"].dt.tz_convert(LOCAL_TZ)
            decades_table = decades_table.sort_values("first_listen", ascending=True)
            decades_table["First Listen"] = decades_table["first_listen"].dt.strftime("%d/%m/%Y %H:%M:%S")
            decades_table = decades_table[["decade", "First Listen"]].head(global_rows_to_show)
            st.markdown("### 🗓️ New Decades")
            st.dataframe(decades_table, hide_index=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=summary_full["Period"], y=summary_full["Minutes"], mode="lines+markers", name="Minutes", line=dict(color="#1f77b4")),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=summary_full["Period"], y=summary_full["Plays"], mode="lines+markers", name="Plays", line=dict(color="#ff7f0e")),
            secondary_y=True
        )
        fig.update_layout(title_text="Minutos y Reproducciones en el Tiempo", legend_title_text="Métrica")
        fig.update_xaxes(title_text="Fecha")
        fig.update_yaxes(title_text="Minutes", secondary_y=False)
        fig.update_yaxes(title_text="Plays", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
