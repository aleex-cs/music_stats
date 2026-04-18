import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import apply_time_filter

def time_of_hour(df, start_date, end_date, period_filter):
    df_filtered = df[(df["datetime"] >= start_date) & (df["datetime"] <= end_date)]
    df_filtered = apply_time_filter(df_filtered, period_filter)

    df_filtered = df_filtered.copy()
    df_filtered["hour"] = df_filtered["datetime"].dt.hour
    summary = df_filtered.groupby("hour")["duration"].sum() / 60
    summary = summary.round(2).reset_index()

    fig = px.bar(
        summary,
        x="hour",
        y="duration",
        labels={"duration": "Minutes", "hour": "Hour"},
        title=f"Listening Time by Hour ({period_filter})"
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

def time_of_weekday(df, start_date, end_date, period_filter):
    df_filtered = df[(df["datetime"] >= start_date) & (df["datetime"] <= end_date)]
    df_filtered = apply_time_filter(df_filtered, period_filter)

    df_filtered = df_filtered.copy()
    df_filtered["weekday"] = df_filtered["datetime"].dt.day_name()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    summary = df_filtered.groupby("weekday")["duration"].sum() / 60
    summary = summary.round(2).reindex(order).reset_index()

    fig = px.bar(
        summary,
        x="weekday",
        y="duration",
        labels={"duration": "Minutes", "weekday": "Weekday"},
        title=f"Listening Time by Weekday ({period_filter})"
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

def render_github_heatmap(df, start_date, end_date, period_filter):
    df_hm = df[(df["datetime"] >= start_date) & (df["datetime"] <= end_date)]
    df_hm = apply_time_filter(df_hm, period_filter).copy()
    
    if df_hm.empty:
        return
        
    df_hm["date"] = df_hm["datetime"].dt.date
    daily_stats = df_hm.groupby("date")["duration"].sum() / 60.0
    daily_stats = daily_stats.reset_index()
    daily_stats["date"] = pd.to_datetime(daily_stats["date"])
    
    min_date = daily_stats["date"].min()
    max_date = daily_stats["date"].max()
    all_days = pd.date_range(min_date, max_date)
    
    heatmap_df = pd.DataFrame({"date": all_days})
    heatmap_df = heatmap_df.merge(daily_stats, on="date", how="left").fillna({"duration": 0})
    
    heatmap_df["weekday"] = heatmap_df["date"].dt.dayofweek
    heatmap_df["week"] = heatmap_df["date"].dt.isocalendar().week
    heatmap_df["year"] = heatmap_df["date"].dt.isocalendar().year
    
    heatmap_df["week_str"] = heatmap_df["year"].astype(str) + "-W" + heatmap_df["week"].astype(str).str.zfill(2)
    
    pivot_table = heatmap_df.pivot(index="weekday", columns="week_str", values="duration")
    pivot_table = pivot_table.reindex([0,1,2,3,4,5,6], fill_value=0)
    
    fig = px.imshow(
        pivot_table.values,
        labels=dict(x="Week", y="Weekday", color="Minutes"),
        x=pivot_table.columns,
        y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        color_continuous_scale=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        title="Activity Heatmap (GitHub Style)"
    )
    
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117"
    )
    fig.update_traces(xgap=3, ygap=3)
    st.plotly_chart(fig, use_container_width=True)

def render_time_patterns(df, global_start, global_end, global_time_filter):
    # CLOCK CHART — Listening Time by Hour (Radial)
    df_clock = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_clock = apply_time_filter(df_clock, global_time_filter).copy()

    if not df_clock.empty:
        df_clock["hour"] = df_clock["datetime"].dt.hour
        summary_clock = df_clock.groupby("hour")["duration"].sum().reset_index()
        summary_clock["minutes"] = summary_clock["duration"] / 60
        summary_clock["hour_str"] = summary_clock["hour"].astype(str)
        hour_order = [str(h) for h in range(24)]

        fig_clock = px.line_polar(
            summary_clock,
            r="minutes",
            theta="hour_str",
            category_orders={"hour_str": hour_order},
            line_close=True,
            markers=True,
            title="Clock Chart — Minutes Listened by Hour",
        )

        fig_clock.update_traces(
            line=dict(color="#FF4B4B", width=3),
            marker=dict(size=6, color="#FF4B4B")
        )

        fig_clock.update_layout(
            polar=dict(
                bgcolor="#111825",   
                radialaxis=dict(
                            showticklabels=False,
                            ticks='',
                            showgrid=True,
                            gridcolor="#3a4750",
                            showline=False,
                        ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,
                    color="white",
                    gridcolor="#3a4750",
                ),
            ),
            font=dict(color="white")
        )

        st.plotly_chart(fig_clock, use_container_width=True)
    else:
        st.info("No hay datos para el rango seleccionado.")

    time_of_hour(df, global_start, global_end, global_time_filter)
    time_of_weekday(df, global_start, global_end, global_time_filter)

    # HEATMAP 1 — Hora (filas) × Día de la semana (columnas)
    df_hm = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_hm = apply_time_filter(df_hm, global_time_filter).copy()
    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    if not df_hm.empty:
        df_hm["hour"] = df_hm["datetime"].dt.hour
        df_hm["weekday"] = df_hm["datetime"].dt.day_name()

        heatmap1 = (
            df_hm.groupby(["hour", "weekday"])["duration"].sum()
            .reset_index()
            .pivot(index="hour", columns="weekday", values="duration")
            .reindex(columns=weekday_order, fill_value=0)
        ) / 60
        heatmap1 = heatmap1.fillna(0).round(2)
        zmax1 = heatmap1.values.max() if heatmap1.values.size > 0 else 1

        fig_hm1 = px.imshow(
            heatmap1.values,
            x=heatmap1.columns,
            y=heatmap1.index,
            labels=dict(x="Weekday", y="Hour", color="Minutes"),
            title="Heatmap — Minutes by Hour × Weekday",
            color_continuous_scale=["#0d1b2a", "#3b1c5a", "#b52a3a", "#ff6e48", "#ffe04b"],
            zmin=0,
            zmax=zmax1,
            aspect="auto"
        )
        fig_hm1.update_xaxes(side="top")
        st.plotly_chart(fig_hm1, use_container_width=True)

    # HEATMAP 2 — Día (filas) × Mes (columnas)
    df_hm2 = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_hm2 = apply_time_filter(df_hm2, global_time_filter).copy()

    if not df_hm2.empty:
        df_hm2["weekday"] = df_hm2["datetime"].dt.day_name()
        df_hm2["month"] = df_hm2["datetime"].dt.strftime("%Y-%m")

        heatmap2 = (
            df_hm2.groupby(["weekday", "month"])["duration"].sum()
            .reset_index()
            .pivot(index="weekday", columns="month", values="duration")
            .reindex(index=weekday_order, fill_value=0)
        ) / 60
        heatmap2 = heatmap2.fillna(0).round(2)
        zmax2 = heatmap2.values.max() if heatmap2.values.size > 0 else 1

        fig_hm2 = px.imshow(
            heatmap2.values,
            x=heatmap2.columns,
            y=heatmap2.index,
            labels=dict(x="Month", y="Weekday", color="Minutes"),
            title="Heatmap — Minutes by Weekday × Month",
            color_continuous_scale=["#0d1b2a", "#3b1c5a", "#b52a3a", "#ff6e48", "#ffe04b"],
            zmin=0,
            zmax=zmax2,
            aspect="auto"
        )
        fig_hm2.update_xaxes(side="top")
        st.plotly_chart(fig_hm2, use_container_width=True)

    # HEATMAP 3 — GitHub Style
    render_github_heatmap(df, global_start, global_end, global_time_filter)
