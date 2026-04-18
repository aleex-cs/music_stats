import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def inject_real_alpine_dark():
    st.markdown("""
        <style>
        .ag-theme-alpine-dark,
        .ag-theme-alpine,
        .ag-theme-streamlit,
        .ag-theme-balham,
        .ag-theme-balham-dark,
        .ag-root-wrapper {
            --ag-foreground-color: #ffffff;
            --ag-background-color: #1b263b;             
            --ag-header-background-color: #0d1b2a;      
            --ag-header-foreground-color: #ffffff;

            --ag-odd-row-background-color: #1e2a3e;     
            --ag-row-hover-color: #24344d;              

            --ag-border-color: rgba(255,255,255,0.10);  
            --ag-selected-row-background-color: #2b3d57;

            --ag-font-size: 14px !important;
            --ag-font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;

            --ag-header-cell-hover-background-color: #152238;
            --ag-header-row-background-color: #0d1b2a;
        }

        .ag-root-wrapper {
            border-radius: 10px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        .ag-header, .ag-header-row {
            height: 38px !important;
            min-height: 38px !important;
        }
        .ag-cell {
            padding: 6px 10px !important;
        }

        .ag-input-field-input, .ag-text-field-input {
            background-color: rgba(255,255,255,0.06) !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }

        .ag-body-horizontal-scroll, .ag-body-vertical-scroll {
            scrollbar-width: thin;
        }
        .ag-body-horizontal-scroll::-webkit-scrollbar,
        .ag-body-vertical-scroll::-webkit-scrollbar { height: 8px; width: 8px; }
        .ag-body-horizontal-scroll::-webkit-scrollbar-thumb,
        .ag-body-vertical-scroll::-webkit-scrollbar-thumb {
            background: rgba(128,128,128,0.35);
            border-radius: 6px;
        }
        
        .ag-theme-alpine-dark .ag-row,
        .ag-row {
            background-color: #1b263b !important;   
            color: white !important;
        }

        .ag-theme-alpine-dark .ag-row:hover,
        .ag-row:hover {
            background-color: #24344d !important;    
        }

        .ag-row-even, 
        .ag-row-odd {
            background-color: #1b263b !important;
        }

        .ag-theme-alpine-dark .ag-header,
        .ag-theme-alpine-dark .ag-header-viewport,
        .ag-theme-alpine-dark .ag-header-row,
        .ag-theme-alpine-dark .ag-header-cell,
        .ag-theme-alpine-dark .ag-floating-filter {
            background-color: #0d1b2a !important;
            background-image: none !important;  
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_plotly_theme():
    base = (st.get_option("theme.base") or "light").lower()
    px.defaults.template = "plotly_dark" if base == "dark" else "plotly_white"
    px.defaults.color_discrete_sequence = ["#FF4B4B"]
    px.defaults.color_continuous_scale = ["#FF4B4B", "#7F2525"]

AGGRID_CUSTOM_CSS = {
    ".ag-root-wrapper": {
        "background-color": "#1b263b !important",
    },
    ".ag-header": {
        "background-color": "#0d1b2a !important",
        "background-image": "none !important",
        "color": "#ffffff !important",
        "border-bottom": "1px solid rgba(255,255,255,0.12) !important",
    },
    ".ag-header-viewport": {
        "background-color": "#0d1b2a !important",
        "background-image": "none !important",
    },
    ".ag-header-row": {
        "background-color": "#0d1b2a !important",
    },
    ".ag-header-cell": {
        "background-color": "#0d1b2a !important",
        "color": "#ffffff !important",
    },
    ".ag-floating-filter": {
        "background-color": "#0d1b2a !important",
        "color": "#ffffff !important",
    },
    ".ag-center-cols-container": {
        "background-color": "#1b263b !important",
        "color": "#ffffff !important",
    },
    ".ag-row-odd": {
        "background-color": "#1e2a3e !important",
    },
    ".ag-row-hover": {
        "background-color": "#24344d !important",
    },
    ".ag-root": {
        "border-color": "rgba(255,255,255,0.10) !important",
    },
    ".ag-input-field-input": {
        "background-color": "rgba(255,255,255,0.06) !important",
        "color": "#ffffff !important",
        "border": "1px solid rgba(255,255,255,0.12) !important",
        "border-radius": "6px !important",
    },
}

def display_aggrid(df_summary, container_id: str):
    if df_summary.empty:
        st.write("No data")
        return

    df_summary = df_summary.copy()

    for c in df_summary.select_dtypes(include=["datetime"]).columns:
        df_summary.loc[:, c] = df_summary[c].dt.strftime("%Y-%m-%d")

    for c in df_summary.select_dtypes(include=["float", "int"]).columns:
        df_summary.loc[:, c] = df_summary[c].round(2)

    gb = GridOptionsBuilder.from_dataframe(df_summary)
    gb.configure_default_column(filter=True, sortable=True, resizable=True)

    for c in df_summary.select_dtypes(include=["number"]).columns:
        gb.configure_column(
            c,
            filter="agNumberColumnFilter",
            type=["numericColumn"],
            cellStyle={"textAlign": "right"},
        )
    for c in df_summary.select_dtypes(include=["object"]).columns:
        gb.configure_column(c, filter="agTextColumnFilter")

    if "Minutes%" in df_summary.columns:
        gb.configure_column(
            "Minutes%",
            filter="agNumberColumnFilter",
            type=["numericColumn"],
            cellStyle={"textAlign": "right"},
            valueFormatter=JsCode("function(params){ return (params.value==null)?'':(Number(params.value).toFixed(2)+'%'); }"),
        )
    if "Plays%" in df_summary.columns:
        gb.configure_column(
            "Plays%",
            filter="agNumberColumnFilter",
            type=["numericColumn"],
            cellStyle={"textAlign": "right"},
            valueFormatter=JsCode("function(params){ return (params.value==null)?'':(Number(params.value).toFixed(2)+'%'); }"),
        )

    on_first_data_rendered = JsCode("""
    function(params) {
        params.api.sizeColumnsToFit();
        setTimeout(function() { params.api.sizeColumnsToFit(); }, 0);
    }
    """)

    on_grid_size_changed = JsCode("""
    function(params) {
        params.api.sizeColumnsToFit();
        setTimeout(function() { params.api.sizeColumnsToFit(); }, 50);
    }
    """)

    row_style = JsCode("""
    function(params) {
      return { backgroundColor: '#1b263b', color: '#ffffff' };
    }
    """)

    gb.configure_grid_options(
        rowHeight=32,
        headerHeight=38,
        suppressCellFocus=True,
        rowSelection="single",
        enableBrowserTooltips=True,
        animateRows=True,
        domLayout="autoHeight",
        getRowStyle=row_style,
        onFirstDataRendered=on_first_data_rendered,
        onGridSizeChanged=on_grid_size_changed,
        suppressColumnVirtualisation=True,
    )

    grid_options = gb.build()

    st.markdown(f"""
    <style>
    #{container_id} .ag-header,
    #{container_id} .ag-header-viewport,
    #{container_id} .ag-header-row,
    #{container_id} .ag-header-cell,
    #{container_id} .ag-floating-filter {{
        background-color: #0d1b2a !important;
        background-image: none !important;
        color: #ffffff !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div id="{container_id}">', unsafe_allow_html=True)

    AgGrid(
        df_summary,
        gridOptions=grid_options,
        fit_columns_on_grid_load=False,
        theme="alpine-dark",
        allow_unsafe_jscode=True,
        custom_css=AGGRID_CUSTOM_CSS,
    )
    st.markdown('</div>', unsafe_allow_html=True)

def build_evolution_figure(summary_df: pd.DataFrame, top_labels: list, label_col: str, title: str, x_title: str):
    fig = go.Figure()
    colors = px.colors.qualitative.Safe
    summary_df = summary_df.sort_values("Period")

    for i, label in enumerate(top_labels):
        df_line = summary_df[summary_df[label_col] == label]
        fig.add_trace(go.Scatter(
            x=df_line["Period"],
            y=df_line["Minutes"],
            mode="lines+markers",
            name=label,
            marker=dict(size=8),
            line=dict(width=3, color=colors[i % len(colors)]),
            hovertemplate="%{y:.2f} min<extra>%{fullData.name}</extra>"
        ))

    fig.update_layout(
        template="plotly_dark",
        title=title,
        xaxis_title=x_title,
        yaxis_title="Minutes",
        hovermode="x unified",
    )
    return fig
