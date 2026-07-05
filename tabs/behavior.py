import streamlit as st
import pandas as pd
from utils.helpers import apply_time_filter, add_period_column, LOCAL_TZ, format_period
from utils.ui import build_evolution_figure
from utils.localization import get_text
from utils.bar_race import generate_bar_race,FRAMES_PER_PERIOD 


def _render_bar_race(df_ev: pd.DataFrame, period_col: str, entity_col: str,
                     minutes_col: str, title: str, cache_key: str):
    """
    Renders a bar chart race video inside an expander.
    Generates the video lazily (only when the user clicks Generate).
    """

    with st.expander(f"🎬 Bar Chart Race — {title}"):
        if st.button("▶ Generate video", key=f"btn_race_{cache_key}"):
            progress_bar = st.progress(0, text="Starting…")
            status_text = st.empty()

            def on_progress(current, total):
                pct = current / total
                elapsed_periods = current / FRAMES_PER_PERIOD   # approx
                progress_bar.progress(pct, text=f"Rendering… {current}/{total} frames ({pct*100:.0f}%)")

            with st.spinner(""):
                video_bytes = generate_bar_race(
                    df_all=df_ev,
                    period_col=period_col,
                    entity_col=entity_col,
                    minutes_col=minutes_col,
                    title=title,
                    progress_callback=on_progress,
                )
            progress_bar.progress(1.0, text="✅ Done!")
            st.session_state[f"race_video_{cache_key}"] = video_bytes

        if f"race_video_{cache_key}" in st.session_state:
            st.video(st.session_state[f"race_video_{cache_key}"])

def render_behavior(df, df_genre, global_start, global_end, global_time_filter,
                    global_period, global_rows_to_show, global_top_n, lang="en"):

    st.markdown(
        f"<h1 style='text-align: center; color: #FF4B4B; font-size: 3.5rem;'>"
        f"{get_text('tabs.dna', lang)} 🧠</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h4 style='text-align: center; color: #b3b3b3;'>"
        f"{get_text('behavior.subtitle', lang)}</h4>",
        unsafe_allow_html=True,
    )
    st.write("---")

    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter)

    from utils.helpers import calculate_sessions

    # ── Sessions ──────────────────────────────────────────────────────────────
    st.markdown("### 🧠 Deep Density Analysis (Listening Sessions)")
    st.markdown("*(A session ends when you pause listening for more than 30 minutes)*")

    sessions = calculate_sessions(df_filtered, max_gap_minutes=30)

    if not sessions.empty:
        avg_session = round(sessions["session_minutes"].mean())
        max_session = sessions.loc[sessions["session_minutes"].idxmax()]
        avg_tracks = round(sessions["track_count"].mean())

        c1, c2, c3 = st.columns(3)
        c1.metric("Average Session Length", f"{avg_session} mins")
        c2.metric("Average Tracks per Session", avg_tracks)

        longest_mins = round(max_session["session_minutes"])
        longest_date = max_session["start_time"].strftime("%Y-%m-%d %H:%M")
        c3.metric("Longest Session (Marathon)", f"{longest_mins} mins",
                  help=f"Started at {longest_date}")

        sessions["start_hour"] = (sessions["start_time"].dt.hour
                                  + sessions["start_time"].dt.minute / 60.0)
        sessions["date"] = sessions["start_time"].dt.date

        import plotly.express as px
        fig_scatter = px.scatter(
            sessions,
            x="date", y="start_hour",
            size="session_minutes", color="session_minutes",
            hover_data=["track_count"],
            labels={"date": "Date", "start_hour": "Time of Day (Hour)",
                    "session_minutes": "Duration (mins)"},
            title="Listening Marathons over Time",
            color_continuous_scale="Inferno",
        )
        fig_scatter.update_layout(yaxis=dict(autorange="reversed",
                                             tickmode="linear", dtick=4))
        st.plotly_chart(fig_scatter, use_container_width=True)

        with st.expander("Show Raw Session Data"):
            cols_to_show = ["start_time", "end_time", "track_count", "session_minutes"]
            display_sessions = (
                sessions[cols_to_show]
                .sort_values("session_minutes", ascending=False)
                .head(global_rows_to_show)
                .copy()
            )
            display_sessions["start_time"] = display_sessions["start_time"].dt.strftime(
                "%Y-%m-%d %H:%M:%S")
            display_sessions["end_time"] = display_sessions["end_time"].dt.strftime(
                "%Y-%m-%d %H:%M:%S")
            display_sessions["session_minutes"] = display_sessions["session_minutes"].round(1)
            st.dataframe(display_sessions, hide_index=True, use_container_width=True)
    else:
        st.info("Not enough data to calculate sessions.")

    x_title = {"day": "Day", "week": "Week (start date)",
                "month": "Month", "year": "Year"}.get(global_period, "Period")

    # ── Track Evolution ───────────────────────────────────────────────────────
    df_track_ev = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_track_ev = apply_time_filter(df_track_ev, global_time_filter).copy()

    if not df_track_ev.empty:
        df_track_ev = add_period_column(df_track_ev, global_period, LOCAL_TZ)

        all_periods_ordered = sorted(df_track_ev["Period"].unique())
        ordered_periods = [format_period(p) for p in all_periods_ordered]

        top_tracks = (
            df_track_ev.groupby("track")["duration"]
            .sum().sort_values(ascending=False)
            .head(global_top_n).index
        )

        summary_tracks = (
            df_track_ev.groupby(["Period", "track"])["duration"]
            .sum().reset_index()
            .rename(columns={"track": "Track"})
        )
        summary_tracks["Minutes"] = summary_tracks["duration"] / 60.0
        summary_tracks = summary_tracks.sort_values("Period")

        race_tracks = summary_tracks.copy()
        race_tracks["Period"] = race_tracks["Period"].apply(format_period).astype(str)
        summary_tracks["Period"] = summary_tracks["Period"].apply(format_period).astype(str)

        fig_tracks = build_evolution_figure(
            summary_tracks[summary_tracks["Track"].isin(top_tracks)],
            list(top_tracks), "Track",
            f"Track Listening Evolution — grouped by {global_period}",
            x_title, x_order=ordered_periods,
        )
        st.plotly_chart(fig_tracks, use_container_width=True)

        _render_bar_race(
            df_ev=race_tracks,
            period_col="Period", entity_col="Track", minutes_col="Minutes",
            title=f"Track Listening Race — {global_period}",
            cache_key=f"track_{global_start}_{global_end}_{global_period}",
        )
    else:
        st.info("No track data for the selected range/period/shift.")

    # ── Artist Evolution ──────────────────────────────────────────────────────
    df_artist_ev = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_artist_ev = apply_time_filter(df_artist_ev, global_time_filter).copy()

    if not df_artist_ev.empty:
        df_artist_ev = add_period_column(df_artist_ev, global_period, LOCAL_TZ)

        all_periods_ordered = sorted(df_artist_ev["Period"].unique())
        ordered_periods = [format_period(p) for p in all_periods_ordered]

        top_artists = (
            df_artist_ev.groupby("artist")["duration"]
            .sum().sort_values(ascending=False)
            .head(global_top_n).index
        )

        summary_artists = (
            df_artist_ev.groupby(["Period", "artist"])["duration"]
            .sum().reset_index()
            .rename(columns={"artist": "Artist"})
        )
        summary_artists["Minutes"] = summary_artists["duration"] / 60.0
        summary_artists = summary_artists.sort_values("Period")

        race_artists = summary_artists.copy()
        race_artists["Period"] = race_artists["Period"].apply(format_period).astype(str)
        summary_artists["Period"] = summary_artists["Period"].apply(format_period).astype(str)

        fig_artists = build_evolution_figure(
            summary_artists[summary_artists["Artist"].isin(top_artists)],
            list(top_artists), "Artist",
            f"Artist Listening Evolution — grouped by {global_period}",
            x_title, x_order=ordered_periods,
        )
        st.plotly_chart(fig_artists, use_container_width=True)

        _render_bar_race(
            df_ev=race_artists,
            period_col="Period", entity_col="Artist", minutes_col="Minutes",
            title=f"Artist Listening Race — {global_period}",
            cache_key=f"artist_{global_start}_{global_end}_{global_period}",
        )
    else:
        st.info("No artist data for the selected range/period/shift.")

    # ── Album Evolution ───────────────────────────────────────────────────────
    df_album_ev = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_album_ev = apply_time_filter(df_album_ev, global_time_filter).copy()
    df_album_ev = df_album_ev[df_album_ev["album_clean"].notna()]

    if not df_album_ev.empty:
        df_album_ev = add_period_column(df_album_ev, global_period, LOCAL_TZ)

        all_periods_ordered = sorted(df_album_ev["Period"].unique())
        ordered_periods = [format_period(p) for p in all_periods_ordered]

        top_albums = (
            df_album_ev.groupby("album_clean")["duration"]
            .sum().sort_values(ascending=False)
            .head(global_top_n).index
        )

        summary_albums = (
            df_album_ev.groupby(["Period", "album_clean"])["duration"]
            .sum().reset_index()
            .rename(columns={"album_clean": "Album"})
        )
        summary_albums["Minutes"] = summary_albums["duration"] / 60.0
        summary_albums = summary_albums.sort_values("Period")

        race_albums = summary_albums.copy()
        race_albums["Period"] = race_albums["Period"].apply(format_period).astype(str)
        summary_albums["Period"] = summary_albums["Period"].apply(format_period).astype(str)

        fig_albums = build_evolution_figure(
            summary_albums[summary_albums["Album"].isin(top_albums)],
            list(top_albums), "Album",
            f"Album Listening Evolution — grouped by {global_period}",
            x_title, x_order=ordered_periods,
        )
        st.plotly_chart(fig_albums, use_container_width=True)

        _render_bar_race(
            df_ev=race_albums,
            period_col="Period", entity_col="Album", minutes_col="Minutes",
            title=f"Album Listening Race — {global_period}",
            cache_key=f"album_{global_start}_{global_end}_{global_period}",
        )
    else:
        st.info("No album data for the selected range/period/shift.")

    # ── Genre Evolution ───────────────────────────────────────────────────────
    df_gen_ev = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gen_ev = apply_time_filter(df_gen_ev, global_time_filter).copy()
    df_gen_ev = df_gen_ev[df_gen_ev["genre_single"].notna()]

    if not df_gen_ev.empty:
        df_gen_ev = add_period_column(df_gen_ev, global_period, LOCAL_TZ)

        all_periods_ordered = sorted(df_gen_ev["Period"].unique())
        ordered_periods = [format_period(p) for p in all_periods_ordered]

        top_genres = (
            df_gen_ev.groupby("genre_single")["duration"]
            .sum().sort_values(ascending=False)
            .head(global_top_n).index
        )

        summary_genres = (
            df_gen_ev.groupby(["Period", "genre_single"])["duration"]
            .sum().reset_index()
            .rename(columns={"genre_single": "Genre"})
        )
        summary_genres["Minutes"] = summary_genres["duration"] / 60.0
        summary_genres = summary_genres.sort_values("Period")

        race_genres = summary_genres.copy()
        race_genres["Period"] = race_genres["Period"].apply(format_period).astype(str)
        summary_genres["Period"] = summary_genres["Period"].apply(format_period).astype(str)

        fig_genres = build_evolution_figure(
            summary_genres[summary_genres["Genre"].isin(top_genres)],
            list(top_genres), "Genre",
            f"Genre Listening Evolution — grouped by {global_period}",
            x_title, x_order=ordered_periods,
        )
        st.plotly_chart(fig_genres, use_container_width=True)

        _render_bar_race(
            df_ev=race_genres,
            period_col="Period", entity_col="Genre", minutes_col="Minutes",
            title=f"Genre Listening Race — {global_period}",
            cache_key=f"genre_{global_start}_{global_end}_{global_period}",
        )
    else:
        st.info("No genre data for the selected range/period/shift.")

    # ── Dominant artist per month (unchanged) ─────────────────────────────────
    df_month = df_filtered.copy()
    df_month["month"] = df_month["datetime"].dt.to_period("M")
    dominant = (
        df_month.groupby(["month", "artist"])["duration"]
        .sum().reset_index()
    )
    if not dominant.empty:
        idx = dominant.groupby("month")["duration"].idxmax()
        dominant = dominant.loc[idx]
        dominant["minutes"] = dominant["duration"] / 60