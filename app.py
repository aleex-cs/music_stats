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

st.set_page_config(page_title="Music Stats", layout="wide")

inject_real_alpine_dark()
apply_plotly_theme()

df, df_genre = get_processed_data()

# Global Sidebar Filters
st.sidebar.title("Filtros Globales")

quick_options = [
    "Todo", "Personalizado", "Último día", "Última semana", "Último mes",
    "Últimos 3 meses", "Últimos 6 meses", "YTD (año en curso)",
    "Último año", "Último día natural", "Última semana natural", "Último mes natural",
]

if "quick_range" not in st.session_state:
    st.session_state.quick_range = "Todo"

quick_range = st.sidebar.selectbox("Quick range", quick_options, key="quick_range")

is_custom = quick_range == "Personalizado"

if is_custom:
    default_start = datetime(2025, 1, 1)
    default_end = datetime.now()
else:
    q_start, q_end = get_quick_range(quick_range, tz_name=LOCAL_TZ)
    if quick_range == "Todo" and not df.empty:
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
        st.session_state.quick_range = "Personalizado"
        st.rerun()

if st.session_state.quick_range == "Personalizado":
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
global_top_n = st.sidebar.slider("Series en gráficos de evolución (Top N)", min_value=3, max_value=20, value=5, step=1, help="Número de series (líneas) a mostrar en los gráficos de evolución para artistas, tracks, álbumes y géneros.")

df = df[df["year_release"].isna() | df["year_release"].between(year_range[0], year_range[1])]

df_genre = df_genre.merge(
    df[["datetime", "track", "artist", "album", "year_release"]],
    on=["datetime", "track", "artist", "album"],
    how="left"
)

if st.session_state.quick_range != "Personalizado":
    st.sidebar.caption(
        f"Aplicando rango: **{st.session_state.quick_range}** → "
        f"{global_start.strftime('%Y-%m-%d %H:%M')} "
        f"a {global_end.strftime('%Y-%m-%d %H:%M')}"
    )

st.title("Music Stats")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Summary",
    "Tracks / Artists / Albums",
    "Time Patterns",
    "Listening Behavior",
    "Searcher",
    "Wrapped (Visual)",
    "Milestones",
    "Visual Insights 📊"
])

with tab1:
    render_summary(df, df_genre, global_start, global_end, global_time_filter, global_period, global_rows_to_show)

with tab2:
    render_data_viewer(df, df_genre, global_start, global_end, global_time_filter, global_rows_to_show)

with tab3:
    render_time_patterns(df, global_start, global_end, global_time_filter)

with tab4:
    render_behavior(df, df_genre, global_start, global_end, global_time_filter, global_period, global_rows_to_show, global_top_n)

with tab5:
    render_searcher(df, global_start, global_end, global_time_filter, global_period, year_min, year_max)

with tab6:
    render_wrapped(df, df_genre, global_start, global_end, global_time_filter)

with tab7:
    render_milestones(df, global_start, global_end, global_time_filter)

with tab8:
    render_visuals(df, df_genre, global_start, global_end, global_time_filter)