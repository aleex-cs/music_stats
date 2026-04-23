import streamlit as st
from datetime import datetime
import pandas as pd

from utils.ui import inject_real_alpine_dark, apply_plotly_theme
from utils.data import get_processed_data
from utils.helpers import get_quick_range, LOCAL_TZ

from tabs.summary import render_summary
from tabs.data_viewer import render_data_viewer
from tabs.time_patterns import render_time_patterns
from tabs.behavior import render_behavior
from tabs.searcher import render_searcher
from tabs.wrapped import render_wrapped
from tabs.milestones import render_milestones
from tabs.visuals import render_visuals
from tabs.home import render_home
from utils.localization import get_text

st.set_page_config(page_title="Music Stats", layout="wide")

inject_real_alpine_dark()
apply_plotly_theme()

df, df_genre = get_processed_data()

# Global Sidebar Filters
st.sidebar.title("Music Stats")
lang = st.sidebar.selectbox("Language / Idioma", ["en", "es"], index=0)
st.session_state.lang = lang

st.sidebar.title(get_text("sidebar_filters", lang))

quick_options = [
    "All", "Custom", "Last Day", "Last Week", "Last Month",
    "Last 3 Months", "Last 6 Months", "YTD (Year to Date)",
    "Last Year", "Last Natural Day", "Last Natural Week", "Last Natural Month",
]

if "quick_range" not in st.session_state:
    st.session_state.quick_range = "All"

quick_range = st.sidebar.selectbox("Quick range", quick_options, key="quick_range")

is_custom = quick_range == "Custom"

if is_custom:
    default_start = datetime(2025, 1, 1)
    default_end = datetime.now()
else:
    q_start, q_end = get_quick_range(quick_range, tz_name=LOCAL_TZ)
    if quick_range == "All" and not df.empty:
        q_start = df["datetime"].min()
        q_end   = df["datetime"].max()
    default_start = q_start
    default_end   = q_end

if "start_date" not in st.session_state:
    st.session_state.start_date = default_start.date()

if "end_date" not in st.session_state:
    st.session_state.end_date = default_end.date()

if not is_custom:
    st.session_state.start_date = default_start.date()
    st.session_state.end_date   = default_end.date()

start_date_input = st.sidebar.date_input("Start Date", key="start_date", disabled=not is_custom)
end_date_input = st.sidebar.date_input("End Date", key="end_date", disabled=not is_custom)

if not is_custom:
    if (st.session_state.start_date != default_start.date() or st.session_state.end_date != default_end.date()):
        st.session_state.quick_range = "Custom"
        st.rerun()

if st.session_state.quick_range == "Custom":
    global_start = pd.to_datetime(st.session_state.start_date).tz_localize(LOCAL_TZ)
    global_end = (pd.to_datetime(st.session_state.end_date).tz_localize(LOCAL_TZ) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
else:
    global_start = default_start
    global_end   = default_end

year_min = int(df["year_release"].min()) if not df.empty and df["year_release"].notna().any() else 1950
year_max = int(df["year_release"].max()) if not df.empty and df["year_release"].notna().any() else datetime.now().year

global_period = st.sidebar.selectbox("Time period", ["day", "week", "month", "year"], index=2)
global_time_filter = st.sidebar.selectbox("Time of day", ["All", "Morning", "Afternoon", "Night"], index=0)
global_rows_to_show = st.sidebar.selectbox("Number of rows", [10, 25, 50, 100, 200, 500], index=0)
year_range = st.sidebar.slider("Release year range", min_value=year_min, max_value=year_max, value=(year_min, year_max), step=1)
global_top_n = st.sidebar.slider("Series in evolution charts (Top N)", min_value=3, max_value=20, value=5, step=1, help="Number of series (lines) to show in the evolution charts for artists, tracks, albums, and genres.")

st.sidebar.markdown("---")
st.sidebar.subheader("Visualization Limits")
global_use_others = st.sidebar.checkbox("Group into 'Others'", value=True, help="If enabled, items outside Top N will be grouped into 'Others'.")
global_n_decades = st.sidebar.slider("Decades", 1, 10, 5)
global_n_genres = st.sidebar.slider("Genres", 1, 50, 15)
global_n_artists = st.sidebar.slider("Artists", 1, 200, 50)
global_n_albums = st.sidebar.slider("Albums", 1, 500, 100)
global_n_tracks = st.sidebar.slider("Tracks", 1, 1000, 300)

df = df[df["year_release"].isna() | df["year_release"].between(year_range[0], year_range[1])]

df_genre = df_genre[df_genre["year_release"].isna() | df_genre["year_release"].between(year_range[0], year_range[1])]

if st.session_state.quick_range != "Custom":
    st.sidebar.caption(
        f"Applying range: **{st.session_state.quick_range}** → "
        f"{global_start.strftime('%Y-%m-%d %H:%M')} "
        f"to {global_end.strftime('%Y-%m-%d %H:%M')}"
    )

st.title("Music Stats")

tab_home, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    get_text("tabs.home", lang),
    get_text("tabs.summary", lang),
    get_text("tabs.rankings", lang),
    get_text("tabs.rhythms", lang),
    get_text("tabs.dna", lang),
    get_text("tabs.explorer", lang),
    get_text("tabs.flashback", lang),
    get_text("tabs.milestones", lang),
    get_text("tabs.galaxy", lang)
])

with tab_home:
    render_home(df, df_genre, global_start, global_end, global_time_filter, lang)

with tab1:
    render_summary(df, df_genre, global_start, global_end, global_time_filter, global_period, global_rows_to_show, lang)

with tab2:
    render_data_viewer(df, df_genre, global_start, global_end, global_time_filter, global_rows_to_show, lang)

with tab3:
    render_time_patterns(df, global_start, global_end, global_time_filter, lang)

with tab4:
    render_behavior(df, df_genre, global_start, global_end, global_time_filter, global_period, global_rows_to_show, global_top_n, lang)

with tab5:
    render_searcher(df, df_genre, global_start, global_end, global_time_filter, global_period, year_min, year_max, lang)

with tab6:
    render_wrapped(df, df_genre, global_start, global_end, global_time_filter, lang)

with tab7:
    render_milestones(df, df_genre, global_start, global_end, global_time_filter, lang)

with tab8:
    render_visuals(
        df, df_genre, global_start, global_end, global_time_filter,
        global_n_decades, global_n_genres, global_n_artists, global_n_albums, global_n_tracks,
        global_use_others
    )