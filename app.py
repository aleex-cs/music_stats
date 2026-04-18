import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import csv
import plotly.graph_objects as go
import re
import unicodedata
import pytz
import calendar
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np

# wordcloud is optional; si no está instalado mostramos mensaje o bar chart
try:
    from wordcloud import WordCloud
    _HAS_WORDCLOUD = True
except ImportError:
    _HAS_WORDCLOUD = False
    # not fatal; tab7 will handle

# =========================
# CONFIG
# =========================

LOCAL_TZ = "Europe/Madrid"

st.set_page_config(page_title="Music Stats", layout="wide")

DATA_PATH = "data/aleex_cs.csv"
DURATIONS_PATH = "data/musica.csv"

def _parse_year_mixed(cell):
    """
    Intenta extraer año (int) desde:
    - 'dd/mm/YYYY' o 'd/m/YY' (con dayfirst=True)
    - 'YYYY'
    - Otros textos: busca un patrón de 4 dígitos [1900..año_actual+1]
    Devuelve None si no se puede inferir.
    """
    if pd.isna(cell):
        return None
    s = str(cell).strip()
    if s == "":
        return None

    # 1) ¿Es un número de 4 dígitos?
    m = re.fullmatch(r"\s*(\d{4})\s*$", s)
    if m:
        y = int(m.group(1))
        return y

    # 2) Intentar parsear fecha con dayfirst
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="raise")
        return int(dt.year)
    except Exception:
        pass

    # 3) Buscar año en el texto
    m = re.search(r"(\d{4})", s)
    if m:
        y = int(m.group(1))
        return y

    return None

def _sanitize_year(y):
    """
    Limpia años imposibles o raros:
    - descarta < 1900
    - descarta > año_actual + 1
    """
    if y is None or pd.isna(y):
        return None
    try:
        y = int(y)
    except Exception:
        return None
    this_year = datetime.now().year
    if y > this_year + 1:
        return None
    return y

# =========================
# THEME / STYLE (ALPINE-DARK REAL + REFUERZO)
# =========================

def inject_real_alpine_dark():
    """
    Inyecta variables del 'alpine-dark' oficial y fuerza los colores
    en cualquier clase de tema que use st-aggrid (streamlit/alpine).
    """
    st.markdown("""
        <style>
        /* Variables auténticas del tema azul oscuro (alpine-dark) */
        .ag-theme-alpine-dark,
        .ag-theme-alpine,
        .ag-theme-streamlit,
        .ag-theme-balham,
        .ag-theme-balham-dark,
        .ag-root-wrapper {
            --ag-foreground-color: #ffffff;
            --ag-background-color: #1b263b;             /* Azul oscuro base */
            --ag-header-background-color: #0d1b2a;      /* Azul más profundo para cabecera */
            --ag-header-foreground-color: #ffffff;

            --ag-odd-row-background-color: #1e2a3e;     /* Filas impares */
            --ag-row-hover-color: #24344d;              /* Hover fila */

            --ag-border-color: rgba(255,255,255,0.10);  /* Bordes sutiles */
            --ag-selected-row-background-color: #2b3d57;

            --ag-font-size: 14px !important;
            --ag-font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;

            /* Variables extra para header si están soportadas */
            --ag-header-cell-hover-background-color: #152238;
            --ag-header-row-background-color: #0d1b2a;
        }

        /* Bordes/sombra y densidad coherente */
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

        /* Inputs de filtro integrados */
        .ag-input-field-input, .ag-text-field-input {
            background-color: rgba(255,255,255,0.06) !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }

        /* Scrollbar discreto */
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
        </style>
    """, unsafe_allow_html=True)

def apply_plotly_theme():
    """Usa plotly_dark si Streamlit está en oscuro; si no, plotly_white."""
    base = (st.get_option("theme.base") or "light").lower()
    px.defaults.template = "plotly_dark" if base == "dark" else "plotly_white"
    px.defaults.color_discrete_sequence = ["#FF4B4B"]
    px.defaults.color_continuous_scale = ["#FF4B4B", "#7F2525"]
    
# Inyectar estilos y tema de gráficos al inicio
inject_real_alpine_dark()
st.markdown("""
<style>
.ag-theme-alpine-dark .ag-row,
.ag-row {
    background-color: #1b263b !important;   /* azul oscuro */
    color: white !important;
}

.ag-theme-alpine-dark .ag-row:hover,
.ag-row:hover {
    background-color: #24344d !important;    /* hover */
}

/* Para eliminar cualquier alternancia odd/even */
.ag-row-even, 
.ag-row-odd {
    background-color: #1b263b !important;
}

/* Refuerzo extra: header sin gradientes blanqueadores */
.ag-theme-alpine-dark .ag-header,
.ag-theme-alpine-dark .ag-header-viewport,
.ag-theme-alpine-dark .ag-header-row,
.ag-theme-alpine-dark .ag-header-cell,
.ag-theme-alpine-dark .ag-floating-filter {
    background-color: #0d1b2a !important;
    background-image: none !important;  /* <- clave */
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)
apply_plotly_theme()

def split_genres(cell):
    """
    Divide un string de géneros por '/', ',', ';' (con o sin espacios),
    normaliza espacios y devuelve una lista limpia.
    """
    if pd.isna(cell):
        return []
    parts = re.split(r'[\/,;]', str(cell))
    genres = [p.strip() for p in parts if p and p.strip()]
    return genres

def _strip_accents(text: str) -> str:
    if text is None:
        return ""
    # Normaliza acentos (útil si algún CSV trae variantes)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def normalize_genre_name(g: str) -> str:
    """
    Normaliza un nombre de género para unificar variantes:
    - quita espacios sobrantes y colapsa múltiples espacios
    - normaliza comillas/acentos raros
    - capitaliza en 'Title Case' (Progressive Rock)
    - aplica diccionario de equivalencias manuales (opcional)
    """
    if g is None or str(g).strip() == "":
        return None
    s = str(g).strip()
    # normaliza espacios
    s = re.sub(r"\s+", " ", s)
    # normaliza acentos raros
    s = _strip_accents(s)
    # Title Case para unificar mayúsculas/minúsculas
    s = s.title()

    # --- Equivalencias manuales (ajusta las que necesites) ---
    # Usa claves en Title Case, tal como queda tras .title()
    EQUIV = {
        # Progresivo
        "Prog Rock": "Progressive Rock",
        "Progressive": "Progressive Rock",
        "Rock Progressif": "Progressive Rock",
        "Progressive Metal": "Progressive Metal",
        
        # Alternativo / Indie
        "Alt Rock": "Alternative Rock",
        "Alternrock": "Alternative Rock",
        "Alternative": "Alternative Rock",
        "Alternative & Indie": "Indie / Alternative",
        "Alternatif Et Inde": "Indie / Alternative",
        "Indie": "Indie / Alternative",
        "Indie/Alternative": "Indie / Alternative",
        "Indie Alternative": "Indie / Alternative",
        
        # Psicodelia
        "Psychedelic": "Psychedelic Rock",
        "Acid Rock": "Psychedelic Rock",
        
        # Blues y Rock
        "Roots Rock Blues": "Blues Rock",
        "Rock And Roll": "Rock & Roll",
        "Pop Rock": "Rock Pop", # Para unificar con el que ya tienes o viceversa
        
        # R&B / Soul
        "Contemporary R&B": "R&B",
        "Jazz Funk Soul": "Soul", # O crear una categoría Jazz/Soul
        
        # Limpieza de "Basura"
        "Miscellaneous": "Unknown",
        "Art": "Unknown" # A menos que sea Art Rock, suele ser una etiqueta mal puesta
    }

    return EQUIV.get(s, s)

def top_genre_by_minutes_full_credit(group):
    """
    Calcula el 'Top Genre' del grupo (periodo) asignando la duración COMPLETA
    de cada reproducción a cada uno de sus géneros (sin repartir).
    Ej.: 250s con géneros 'Rock, Pop' suma 250s a Rock y 250s a Pop.
    """
    if group.empty or "genre" not in group.columns or "duration" not in group.columns:
        return None

    accum = {}
    for _, row in group.iterrows():
        g_list = split_genres(row.get("genre"))
        dur = row.get("duration")
        if pd.isna(dur) or dur <= 0 or not g_list:
            continue
        # ⬇️ CREDITO COMPLETO a cada género
        share = dur
        for g in g_list:
            key = normalize_genre_name(g)
            if key:
                    accum[key] = accum.get(key, 0) + share

    if not accum:
        return None

    return max(accum.items(), key=lambda kv: kv[1])[0]

def get_decade(y):
    if pd.isna(y):
        return None
    try:
        y = int(y)
        decade_start = (y // 10) * 10
        return f"{decade_start}s"
    except:
        return None

def format_first_listen_table(df_new, name_col, datetime_col="datetime"):
    df_out = df_new.copy()

    # Convertimos a zona local si hace falta
    if pd.api.types.is_datetime64_any_dtype(df_out[datetime_col]):
        df_out[datetime_col] = df_out[datetime_col].dt.tz_convert(LOCAL_TZ)

    # Ordenamos por fecha REAL (más antiguo → más nuevo)
    df_out = df_out.sort_values(datetime_col, ascending=True)

    # Formateamos después de ordenar
    df_out["First Listen"] = df_out[datetime_col].dt.strftime("%d/%m/%Y %H:%M:%S")

    # Filtramos columnas
    df_out = df_out[[name_col, "First Listen"]]

    # --- CAMBIO AQUÍ: Capitalizar nombres de columnas ---
    # Opción A: Solo la primera letra de la frase (ej: "First listen")
    # df_out.columns = df_out.columns.str.capitalize()
    
    # Opción B: Primera letra de cada palabra (ej: "First Listen")
    df_out.columns = df_out.columns.str.title()

    return df_out

# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error(f"No se encuentra el archivo: {DATA_PATH}")
        return pd.DataFrame()
    
    # 1. CARGA DE SCROBBLES (aleex_cs.csv) - Detección automática de separador
    try:
        scrobbles = pd.read_csv(DATA_PATH, sep=None, engine='python', encoding='utf-8-sig')
    except:
        scrobbles = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
    
    scrobbles.columns = scrobbles.columns.str.strip()

    # Manejo robusto de la columna de fecha (Evita KeyError: 'date')
    if 'uts' in scrobbles.columns:
        scrobbles["datetime"] = pd.to_datetime(scrobbles["uts"], unit="s", utc=True).dt.tz_convert(LOCAL_TZ)
    elif 'date' in scrobbles.columns:
        scrobbles["datetime"] = pd.to_datetime(scrobbles["date"])
    else:
        # Fallback por si la columna tiene otro nombre (Date, timestamp, etc)
        date_col = next((c for c in scrobbles.columns if 'date' in c.lower() or 'time' in c.lower()), None)
        if date_col:
            scrobbles["datetime"] = pd.to_datetime(scrobbles[date_col], errors='coerce')
        else:
            scrobbles["datetime"] = pd.to_datetime(scrobbles.iloc[:, 0], errors='coerce')

    # Unificación de artistas (Tu lógica original)
    equivalencias = pd.DataFrame({
        "original": [
            # --- TUS ORIGINALES ---
            "Smash (ESP)", "Smash", "Jim Morrison", "Robe.", "I Nomadi",
            "Godspeed You Black Emperor!", "Fito Y Fitipaldis", "Fabrizio de Andre'",
            "Fabrizio De Andre", "Fabrizio De AndrÃ©", "Fabrizio De André",

            # --- Lote 1: VEVO / handles conocidos ---
            "Mark Knopfler & Emmylou Harris", "TheKnackVEVO", "joaquinsabinaVEVO",
            "ZoeVEVO", "calle13vevo", "ojetecalormusica", "fito&fitipaldisVEVO",

            # --- Lote 2: encoding / shows ---
            "Fabrizio De AndrÃ¨", "Guns N' Roses",
            "The Tonight Show starring Jimmy Fallon", "The Game Awards",

            # --- Lote 3: VEVO → artista real ---
            "FrancodeVitaVEVO", "CoezVEVO", "FrancescoGucciniVEVO",
            "Lorenzo Jovanotti Cherubini",

            # --- Lote 4: canales YT / sellos / no-música → _NON_MUSIC_ ---
            "Canal Nostalgia", "Date un Vlog", "Mensaje de Voz",
            "Nacional Records", "Warner Music Spain", "Waves Consumer Electronics",
            "Hank Mc Koy",
        ],
        "canonico": [
            # --- TUS CANÓNICOS ---
            "Smash", "Smash", "The Doors", "Robe", "Nomadi",
            "Godspeed You! Black Emperor", "Fito & Fitipaldis", "Fabrizio De Andre'",
            "Fabrizio De Andre'", "Fabrizio De Andre'", "Fabrizio De Andre'",

            # --- Lote 1 ---
            "Mark Knopfler", "The Knack", "Joaquín Sabina",
            "Zoe", "Calle 13", "Ojete Calor", "Fito & Fitipaldis",

            # --- Lote 2 ---
            "Fabrizio De Andre'", "Guns N' Roses",
            "Jimmy Fallon", "Various Artists",

            # --- Lote 3 ---
            "Franco De Vita", "Coez", "Francesco Guccini",
            "Jovanotti",

            # --- Lote 4 ---
            "_NON_MUSIC_", "_NON_MUSIC_", "_NON_MUSIC_",
            "_NON_MUSIC_", "_NON_MUSIC_", "_NON_MUSIC_",
            "_NON_MUSIC_",
        ]
    })
    for i, row in equivalencias.iterrows():
        scrobbles["artist"] = scrobbles["artist"].replace(row["original"], row["canonico"])
    scrobbles["artist"] = scrobbles["artist"].str.replace(r" - .*", "", regex=True)

    # 2. CARGA DE METADATOS (musica.csv) - Mapeo de columnas español/inglés
    durations = pd.DataFrame()
    if os.path.exists(DURATIONS_PATH):
        try:
            durations = pd.read_csv(DURATIONS_PATH, sep=None, engine='python', encoding='utf-8-sig')
            durations.columns = durations.columns.str.strip()
            
            # Mapeo crítico para evitar KeyError: 'genre' y 'year_release'
            rename_map = {
                "Artista": "artist", "Título": "track", "Género": "genre",
                "Duración(s)": "duration", "Año": "year_raw", "Álbum": "album_musica"
            }
            durations = durations.rename(columns=rename_map)

            # Crear 'year_release' usando tus funciones parseadoras
            if "year_raw" in durations.columns:
                durations["year_release"] = durations["year_raw"].apply(_parse_year_mixed).apply(_sanitize_year)
            
            if "duration" in durations.columns:
                durations["duration"] = pd.to_numeric(durations["duration"], errors="coerce") / 100
        except Exception as e:
            st.warning(f"Error cargando musica.csv: {e}")

    # 3. MERGE (Cruce de datos)
    def normalize_str(s):
        return str(s).strip().lower().replace("’", "'") if pd.notna(s) else ""

    scrobbles["artist_norm"] = scrobbles["artist"].apply(normalize_str)
    scrobbles["track_norm"] = scrobbles["track"].apply(normalize_str)
    
    if not durations.empty:
        durations["artist_norm"] = durations["artist"].apply(normalize_str)
        durations["track_norm"] = durations["track"].apply(normalize_str)
        
        # Columnas que queremos traer
        cols_to_merge = ["artist_norm", "track_norm", "duration", "genre", "year_release"]
        if "album_musica" in durations.columns: cols_to_merge.append("album_musica")
        
        df = scrobbles.merge(
            durations[cols_to_merge].drop_duplicates(["artist_norm", "track_norm"]),
            on=["artist_norm", "track_norm"],
            how="left"
        )
    else:
        df = scrobbles
        df["genre"], df["duration"], df["year_release"] = "Unknown", 0, None

    # 4. UNIFICACIÓN DE ÁLBUMES (album_clean)
    def normalize_album_full(name):
        if pd.isna(name) or str(name).lower() in ["nan", "unknown album", ""]: return "Unknown Album"
        # Limpieza Regex (Disc, Remaster, etc)
        clean = re.sub(r'[\(\[].*?(Disc|Remaster|Edition|Maxicut|Deluxe|Live|Explicit).*?[\)\]]', '', str(name), flags=re.IGNORECASE)
        # Equivalencias específicas
        EQUIV = {
            "The Wall [Disc 1]": "The Wall", "The Wall [Disc 2]": "The Wall",
            "Ummagumma [Studio Album] [Disc 1]": "Ummagumma", "Ummagumma [Live Album] [Disc 2]": "Ummagumma",
            "Making Movies (Australia Maxicut)": "Making Movies", "Love (Disc 1)": "Love", "Love (Disc 2)": "Love"
        }
        return " ".join(EQUIV.get(clean.strip(), clean.strip()).split())

    # Crear album_clean (priorizando el scrobble de Last.fm; musica.csv solo como fallback)
    if "album_musica" in df.columns:
        df["album_clean"] = df["album"].fillna(df["album_musica"]).apply(normalize_album_full)
    else:
        df["album_clean"] = df["album"].apply(normalize_album_full)

    # 5. ASEGURAR COLUMNAS PARA EVITAR CRASHES
    if "genre" not in df.columns: df["genre"] = "Unknown"
    if "year_release" not in df.columns: df["year_release"] = None
    if "duration" not in df.columns: df["duration"] = 0
    
    # Limpiar auxiliares
    df = df.drop(columns=["artist_norm", "track_norm"], errors="ignore")
    return df

# --- BLOQUE DE PROCESAMIENTO TRAS CARGAR ---
df = load_data()

# Eliminar del dataset filas marcadas como no-música (canales YT, sellos, etc.)
df = df[df["artist"] != "_NON_MUSIC_"].copy()

# Detector de tracks con título en formato YouTube
_YT_JUNK_RE = re.compile(
    r'(\(Official\s*(Music\s*)?Video\)'
    r'|\(Official\s*Audio\)'
    r'|\(Videoclip\s*Oficial\)'
    r'|\(Video\s*Oficial\)'
    r'|\(Video\s*Ufficiale\)'
    r'|\(Lyric\s*Video\)'
    r'|\(Lyrics?\))',
    re.IGNORECASE
)

def is_youtube_track(track: str, artist: str = "") -> bool:
    """True si el track parece título de vídeo de YouTube, no un nombre real de canción."""
    if not isinstance(track, str):
        return False
    # Patrón explícito "(Official Audio)", etc.
    if _YT_JUNK_RE.search(track):
        return True
    # Formato "Artista - Canción" donde el artista está en el título
    if isinstance(artist, str) and artist:
        artist_norm = artist.lower().strip()
        track_norm  = track.lower().strip()
        if track_norm.startswith(artist_norm + " - ") or track_norm.startswith(artist_norm + "- "):
            return True
    return False


# Procesar Géneros (Ahora con la columna asegurada)
df_genre = df.copy()
df_genre["genre_single"] = df_genre["genre"].fillna("Unknown").apply(split_genres)
df_genre = df_genre.explode("genre_single")
df_genre = df_genre.dropna(subset=["genre_single"])
df_genre["genre_single"] = df_genre["genre_single"].apply(normalize_genre_name)

# Procesar Décadas (Ahora con year_release asegurada)
df["decade"] = df["year_release"].apply(get_decade)
df_genre["decade"] = df_genre["year_release"].apply(get_decade)
 
df_full = df.copy()  # o aplicar filtros si quieres
df_full.to_csv("full_dataframe_export.csv", index=False, encoding="utf-8")

# =========================
# TIME FILTER (CENTRALIZADO)
# =========================

def apply_time_filter(df, filter_name):
    if filter_name == "Morning":
        return df[(df["datetime"].dt.hour >= 6) & (df["datetime"].dt.hour < 12)]
    elif filter_name == "Afternoon":
        return df[(df["datetime"].dt.hour >= 12) & (df["datetime"].dt.hour < 21)]
    elif filter_name == "Night":
        return df[(df["datetime"].dt.hour >= 21) | (df["datetime"].dt.hour < 6)]
    return df

# =========================
# SUMMARY FUNCTIONS
# =========================

def safe_top_by_minutes(df, col):
    if col not in df.columns or df.empty:
        return None

    summary = (
        df.groupby(col)
        .agg(
            minutes=("duration", "sum"),
            plays=("duration", "count")
        )
        .sort_values(["minutes", "plays"], ascending=False)
    )

    if summary.empty:
        return None

    return summary.index[0]

def top_decade_by_minutes(df):
    if "year_release" not in df.columns:
        return None
    temp = df.dropna(subset=["year_release"]).copy()
    if temp.empty:
        return None
    temp["decade"] = temp["year_release"].apply(get_decade)
    summary = temp.groupby("decade")["duration"].sum()
    return summary.idxmax()

def get_listening_summary(df, period="month"):

    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    if period == "week":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("W").apply(lambda r: r.start_time.date())
    elif period == "day":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.date
    elif period == "month":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("M").apply(lambda r: r.start_time.date())
    elif period == "year":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("Y").apply(lambda r: r.start_time.date())

    df["Period"] = df["Period"].astype(str)

    # --------------------------
    # métricas básicas
    # --------------------------

    summary = df.groupby("Period").agg(
        Minutes=("duration", lambda x: round(x.sum()/60, 2)),
        Plays=("duration", "count"),
        Median_Year=("year_release", "median")
    ).reset_index()

    summary["Median_Year"] = summary["Median_Year"].round(2)

    # --------------------------
    # Top Artist
    # --------------------------

    artist_minutes = (
        df.groupby(["Period","artist"])["duration"]
        .sum()
        .reset_index()
    )

    idx = artist_minutes.groupby("Period")["duration"].idxmax()

    top_artist = artist_minutes.loc[idx, ["Period","artist"]] \
        .rename(columns={"artist":"Top Artist"})

    summary = summary.merge(top_artist, on="Period", how="left")

    # --------------------------
    # Top Track
    # --------------------------

    track_minutes = (
        df.groupby(["Period","track"])["duration"]
        .sum()
        .reset_index()
    )

    idx = track_minutes.groupby("Period")["duration"].idxmax()

    top_track = track_minutes.loc[idx, ["Period","track"]] \
        .rename(columns={"track":"Top Track"})

    summary = summary.merge(top_track, on="Period", how="left")

    # --------------------------
    # Top Album
    # --------------------------

    if "album" in df.columns:

        album_minutes = (
            df.groupby(["Period","album"])["duration"]
            .sum()
            .reset_index()
        )

        idx = album_minutes.groupby("Period")["duration"].idxmax()

        top_album = album_minutes.loc[idx, ["Period","album"]] \
            .rename(columns={"album":"Top Album"})

        summary = summary.merge(top_album, on="Period", how="left")

    # --------------------------
    # Top Decade (por minutos)
    # --------------------------

    temp = df.dropna(subset=["year_release"]).copy()
    temp["decade"] = temp["year_release"].apply(get_decade)

    decade_minutes = (
        temp.groupby(["Period","decade"])["duration"]
        .sum()
        .reset_index()
    )

    idx = decade_minutes.groupby("Period")["duration"].idxmax()

    top_decade = decade_minutes.loc[idx, ["Period","decade"]] \
        .rename(columns={"decade":"Top Decade"})

    summary = summary.merge(top_decade, on="Period", how="left")

    return summary.sort_values("Period")

def summarize(df, col):
    return (
        df.groupby(col)
        .agg(
            Minutes=("duration", lambda x: round(x.sum() / 60, 2)),
            Plays=(col, "count")
        )
        .sort_values("Minutes", ascending=False)
        .reset_index()
    )

def add_share_columns(df_summary):
    """Añade Minutes% y Plays% como porcentaje (numérico, no string)."""
    df_summary = df_summary.copy()
    minutes_total = df_summary["Minutes"].sum()
    plays_total = df_summary["Plays"].sum()

    df_summary["Minutes%"] = (df_summary["Minutes"] / minutes_total * 100) if minutes_total > 0 else 0.0
    df_summary["Plays%"] = (df_summary["Plays"] / plays_total * 100) if plays_total > 0 else 0.0
    return df_summary

def longest_streak(series):
    """
    Devuelve (valor, longitud_racha) para la racha consecutiva más larga
    en una serie.
    """
    if series.empty:
        return None, 0

    best_value = None
    best_len = 0

    current_value = None
    current_len = 0

    for v in series:
        if v == current_value:
            current_len += 1
        else:
            current_value = v
            current_len = 1

        if current_len > best_len:
            best_len = current_len
            best_value = current_value

    return best_value, best_len


    """
    Calcula el 'Top Genre' del grupo (periodo) asignando la duración COMPLETA
    de cada reproducción a cada uno de sus géneros (sin repartir).
    Ej.: 250s con géneros 'Rock, Pop' suma 250s a Rock y 250s a Pop.
    """
    if group.empty or "genre" not in group.columns or "duration" not in group.columns:
        return None

    accum = {}
    for _, row in group.iterrows():
        g_list = split_genres(row.get("genre"))
        dur = row.get("duration")
        if pd.isna(dur) or dur <= 0 or not g_list:
            continue
        # ⬇️ CREDITO COMPLETO a cada género
        share = dur
        for g in g_list:
            key = g.strip()
            accum[key] = accum.get(key, 0) + share

    if not accum:
        return None

    return max(accum.items(), key=lambda kv: kv[1])[0]

def longest_consecutive_block_details(df, key_col):
    """
    Devuelve (valor, tam_bloque, first_dt, last_dt) del bloque consecutivo más largo
    para 'key_col' (p.ej., 'track'/'artist'/'album'), usando el orden temporal real.
    """
    if df.empty or key_col not in df.columns:
        return None, 0, None, None

    s = df.sort_values("datetime").copy()
    s = s[s[key_col].notna()]
    if s.empty:
        return None, 0, None, None

    # Bloques consecutivos por igualdad de valor
    s["prev_val"] = s[key_col].shift()
    s["new_block"] = s[key_col] != s["prev_val"]
    s["block"] = s["new_block"].cumsum()

    # Elegir el (valor, bloque) con mayor tamaño
    counts = s.groupby([key_col, "block"]).size().rename("size").reset_index()
    best_idx = counts["size"].idxmax()
    best = counts.loc[best_idx]
    val = best[key_col]
    block_id = best["block"]
    size = int(best["size"])

    # Timestamps del bloque ganador
    block_df = s[(s[key_col] == val) & (s["block"] == block_id)].sort_values("datetime")
    first_dt = block_df["datetime"].min()
    last_dt  = block_df["datetime"].max()

    return val, size, first_dt, last_dt

def longest_consecutive_block_minutes(df, key_col):
    """
    Devuelve (valor, minutos_totales, first_dt, last_dt) del bloque consecutivo
    más largo por *minutos* para 'key_col', usando el orden temporal real.
    Requiere columna 'duration' en segundos.
    """
    if df.empty or key_col not in df.columns or "duration" not in df.columns:
        return None, 0.0, None, None

    s = df.sort_values("datetime").copy()
    s = s[s[key_col].notna()]
    s = s[s["duration"].notna()]
    if s.empty:
        return None, 0.0, None, None

    # Bloques consecutivos por igualdad de valor
    s["prev_val"] = s[key_col].shift()
    s["new_block"] = s[key_col] != s["prev_val"]
    s["block"] = s["new_block"].cumsum()

    # Sumar duración (segundos) en cada bloque
    dur_blocks = (
        s.groupby([key_col, "block"])["duration"]
         .sum()
         .rename("dur_sec")
         .reset_index()
    )

    best_idx = dur_blocks["dur_sec"].idxmax()
    best = dur_blocks.loc[best_idx]
    val = best[key_col]
    block_id = best["block"]
    dur_min = float(best["dur_sec"]) / 60.0

    block_df = s[(s[key_col] == val) & (s["block"] == block_id)].sort_values("datetime")
    first_dt = block_df["datetime"].min()
    last_dt  = block_df["datetime"].max()

    return val, dur_min, first_dt, last_dt

# =========================
# AGGRID DISPLAY
# =========================

# CSS directo de st-aggrid para forzar colores clave en el árbol interno
AGGRID_CUSTOM_CSS = {
    # Contenedor principal (fondo azul oscuro)
    ".ag-root-wrapper": {
        "background-color": "#1b263b !important",
    },
    # Header con azul más profundo (y sin gradiente)
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
    # Celdas
    ".ag-center-cols-container": {
        "background-color": "#1b263b !important",
        "color": "#ffffff !important",
    },
    # Filas impares
    ".ag-row-odd": {
        "background-color": "#1e2a3e !important",
    },
    # Hover
    ".ag-row-hover": {
        "background-color": "#24344d !important",
    },
    # Bordes
    ".ag-root": {
        "border-color": "rgba(255,255,255,0.10) !important",
    },
    # Inputs de filtros
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

    # Formateo de tipos
    for c in df_summary.select_dtypes(include=["datetime"]).columns:
        df_summary.loc[:, c] = df_summary[c].dt.strftime("%Y-%m-%d")

    for c in df_summary.select_dtypes(include=["float", "int"]).columns:
        df_summary.loc[:, c] = df_summary[c].round(2)

    gb = GridOptionsBuilder.from_dataframe(df_summary)
    gb.configure_default_column(filter=True, sortable=True, resizable=True)

    # Filtros por tipo y alineación
    for c in df_summary.select_dtypes(include=["number"]).columns:
        gb.configure_column(
            c,
            filter="agNumberColumnFilter",
            type=["numericColumn"],
            cellStyle={"textAlign": "right"},
        )
    for c in df_summary.select_dtypes(include=["object"]).columns:
        gb.configure_column(c, filter="agTextColumnFilter")

    # ---- Formateo de porcentajes si existen ----
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

    # ---- JS callbacks para ajuste real de columnas ----
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

    # Estilo de filas
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

    # ---- Scoping por id para máxima especificidad del header ----
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

    # Render dentro de un contenedor con id
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

# =========================
# TIME PATTERNS
# =========================

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

def get_quick_range(preset: str, tz_name: str = "Europe/Madrid"):
    """
    Devuelve (start, end) tz-aware para el preset indicado.
    'end' = ahora (con tz) para presets relativos.
    Para presets 'naturales' devuelve límites del bloque calendario completo.
    """
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)          # tz-aware
    today = now.date()              # fecha local "hoy"

    def at_start_of_day(d):  # 00:00:00
        return tz.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    def at_end_of_day(d):    # 23:59:59.999999
        return tz.localize(datetime(d.year, d.month, d.day, 23, 59, 59, 999999))

    # -------- Presets relativos (rolling windows) --------
    if preset == "Último día":
        start = now - timedelta(days=1)
        end = now
        return start, end

    if preset == "Última semana":
        start = now - timedelta(days=7)
        end = now
        return start, end

    if preset == "Último mes":
        start = now - timedelta(days=30)  # Aproximación robusta sin dependencias externas
        end = now
        return start, end

    if preset == "Últimos 3 meses":
        start = now - timedelta(days=90)
        end = now
        return start, end

    if preset == "Últimos 6 meses":
        start = now - timedelta(days=180)
        end = now
        return start, end

    if preset == "YTD (año en curso)":
        start = tz.localize(datetime(today.year, 1, 1, 0, 0, 0))
        end = now
        return start, end

    if preset == "Último año":
        start = now - timedelta(days=365)
        end = now
        return start, end

    if preset == "Todo":
        # lo ajustaremos al rango real de datos después (si quieres)
        start = tz.localize(datetime(1970, 1, 1, 0, 0, 0))
        end = now
        return start, end

    # -------- Presets naturales (bloques calendario) --------
    if preset == "Último día natural":
        ayer = today - timedelta(days=1)
        start = at_start_of_day(ayer)
        end = at_end_of_day(ayer)
        return start, end

    if preset == "Última semana natural":
        # Semana ISO: Monday=0 ... Sunday=6
        # Queremos la semana completa ANTERIOR a la semana actual.
        weekday = today.weekday()  # 0..6, lunes=0
        # Inicio de semana actual (lunes)
        start_this_week = today - timedelta(days=weekday)
        # Semana anterior:
        start_last_week = start_this_week - timedelta(days=7)
        end_last_week = start_this_week - timedelta(days=1)
        start = at_start_of_day(start_last_week)
        end = at_end_of_day(end_last_week)
        return start, end

    if preset == "Último mes natural":
        # Mes anterior
        year = today.year
        month = today.month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        first_day = datetime(prev_year, prev_month, 1)
        last_day_num = calendar.monthrange(prev_year, prev_month)[1]  # nº de días del mes
        last_day = datetime(prev_year, prev_month, last_day_num)

        start = tz.localize(datetime(first_day.year, first_day.month, first_day.day, 0, 0, 0))
        end = tz.localize(datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59, 999999))
        return start, end

    # Preset no reconocido o "Personalizado"
    return None, None

# =========================
# UI - SIDEBAR GLOBAL + TABS
# =========================

st.sidebar.title("Filtros Globales")

# --- QUICK RANGE ---
quick_options = [
    "Todo",
    "Personalizado",
    "Último día",
    "Última semana",
    "Último mes",
    "Últimos 3 meses",
    "Últimos 6 meses",
    "YTD (año en curso)",
    "Último año",
    "Último día natural",
    "Última semana natural",
    "Último mes natural",
]

# Usamos session_state para permitir cambio automático
if "quick_range" not in st.session_state:
    st.session_state.quick_range = "Todo"

quick_range = st.sidebar.selectbox(
    "Quick range",
    quick_options,
    key="quick_range"
)

# -----------------------------------
# Determinar rango base
# -----------------------------------

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

# -----------------------------------
# DATE INPUTS (con lógica inteligente)
# -----------------------------------

# Inicializamos session_state para fechas
if "start_date" not in st.session_state:
    st.session_state.start_date = default_start.date()

if "end_date" not in st.session_state:
    st.session_state.end_date = default_end.date()

# Si NO es personalizado, forzamos fechas automáticas
if not is_custom:
    st.session_state.start_date = default_start.date()
    st.session_state.end_date   = default_end.date()

start_date_input = st.sidebar.date_input(
    "Start Date",
    key="start_date",
    disabled=not is_custom
)

end_date_input = st.sidebar.date_input(
    "End Date",
    key="end_date",
    disabled=not is_custom
)

# -----------------------------------
# Cambio automático a "Personalizado"
# -----------------------------------

if not is_custom:
    # Si el usuario intenta modificar fechas (cosa rara pero posible por estado),
    # cambiamos automáticamente a Personalizado
    if (
        st.session_state.start_date != default_start.date() or
        st.session_state.end_date   != default_end.date()
    ):
        st.session_state.quick_range = "Personalizado"
        st.rerun()

# -----------------------------------
# Determinar global_start y global_end
# -----------------------------------

if st.session_state.quick_range == "Personalizado":
    global_start = pd.to_datetime(st.session_state.start_date).tz_localize(LOCAL_TZ)
    # Llevamos el end al final del día (23:59:59) para incluir todos los scrobbles de ese día
    global_end = (
        pd.to_datetime(st.session_state.end_date).tz_localize(LOCAL_TZ)
        + pd.Timedelta(days=1)
        - pd.Timedelta(seconds=1)
    )
else:
    global_start = default_start
    global_end   = default_end

# -----------------------------------
# RESTO DE FILTROS
# -----------------------------------

year_min = int(df["year_release"].min()) if df["year_release"].notna().any() else 1950
year_max = int(df["year_release"].max()) if df["year_release"].notna().any() else datetime.now().year

global_period = st.sidebar.selectbox(
    "Time period",
    ["day", "week", "month", "year"],
    index=2
)

global_time_filter = st.sidebar.selectbox(
    "Time of day",
    ["All", "Morning", "Afternoon", "Night"],
    index=0
)

global_rows_to_show = st.sidebar.selectbox(
    "Number of rows",
    [10, 25, 50, 100, 200, 500],
    index=0
)

year_range = st.sidebar.slider(
    "Release year range",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    step=1,
)

global_top_n = st.sidebar.slider(
    "Series en gráficos de evolución (Top N)",
    min_value=3,
    max_value=20,
    value=5,
    step=1,
    help="Número de series (líneas) a mostrar en los gráficos de evolución para artistas, tracks, álbumes y géneros.",
)

# -----------------------------------
# Aplicar filtro por año de lanzamiento
# -----------------------------------

df = df[df["year_release"].isna() | df["year_release"].between(year_range[0], year_range[1])]

df_genre = df_genre.merge(
    df[["datetime", "track", "artist", "album", "year_release"]],
    on=["datetime", "track", "artist", "album"],
    how="left"
)


# -----------------------------------
# Feedback visual
# -----------------------------------

if st.session_state.quick_range != "Personalizado":
    st.sidebar.caption(
        f"Aplicando rango: **{st.session_state.quick_range}** → "
        f"{global_start.strftime('%Y-%m-%d %H:%M')} "
        f"a {global_end.strftime('%Y-%m-%d %H:%M')}"
    )
# =========================
# TABS
# =========================

st.title("Music Stats")
# ampliamos pestañas con secciones extra sin tocar las existentes
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Summary",
    "Tracks / Artists / Albums",
    "Time Patterns",
    "Listening Behavior",
    "Searcher",
    "Heatmap",
    "Wordcloud",
    "Prediction",
    "Genre Network",
    "Diversity"
])

# =========================
# TAB 1 - Listening Summary
# =========================
with tab1:

    # Filtrado por fecha y hora
    df_filtered = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_filtered = apply_time_filter(df_filtered, global_time_filter)

    # Generamos el resumen completo por periodo
    summary_full = get_listening_summary(df_filtered, global_period)
    

    # --------------------------
    # Top Genre por periodo usando df_genre (crédito completo)
    # --------------------------
    df_gf = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gf = apply_time_filter(df_gf, global_time_filter).copy()

    # Asignamos la columna Period con la MISMA lógica que get_listening_summary
    if global_period == "week":
        df_gf["Period"] = df_gf["datetime"].dt.to_period("W").apply(lambda r: r.start_time.tz_localize(LOCAL_TZ).date())
    elif global_period == "day":
        df_gf["Period"] = df_gf["datetime"].dt.tz_convert(LOCAL_TZ).dt.date
    elif global_period == "month":
        df_gf["Period"] = df_gf["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("M").apply(lambda r: r.start_time.date())
    elif global_period == "year":
        df_gf["Period"] = df_gf["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("Y").apply(lambda r: r.start_time.date())

    df_gf["Period"] = df_gf["Period"].astype(str)

    # Sumamos minutos por periodo y género
    genre_per_period = (
        df_gf.groupby(["Period", "genre_single"])["duration"].sum().reset_index()
    )
    # Tomamos el género con mayor duración de cada periodo
    idx = genre_per_period.groupby("Period")["duration"].idxmax()
    top_genre_by_period = (
        genre_per_period.loc[idx, ["Period", "genre_single"]]
        .rename(columns={"genre_single": "Top Genre"})
    )

    # Fusionamos en summary_full (sobrescribe si ya existe "Top Genre")
    summary_full = summary_full.drop(columns=["Top Genre"], errors="ignore") \
                            .merge(top_genre_by_period, on="Period", how="left")

    if not summary_full.empty:

        # --------------------------
        # Period max/min minutos
        # --------------------------
        idx_max_minutes = summary_full["Minutes"].idxmax()
        idx_min_minutes = summary_full["Minutes"].idxmin()

        period_max_minutes_period = summary_full.loc[idx_max_minutes, "Period"]
        period_max_minutes_val = summary_full.loc[idx_max_minutes, "Minutes"]

        period_min_minutes_period = summary_full.loc[idx_min_minutes, "Period"]
        period_min_minutes_val = summary_full.loc[idx_min_minutes, "Minutes"]

        avg_minutes = round(summary_full["Minutes"].mean(), 2)

        # --------------------------
        # Period max/min plays
        # --------------------------
        idx_max_plays = summary_full["Plays"].idxmax()
        idx_min_plays = summary_full["Plays"].idxmin()

        period_max_plays_period = summary_full.loc[idx_max_plays, "Period"]
        period_max_plays_val = summary_full.loc[idx_max_plays, "Plays"]

        period_min_plays_period = summary_full.loc[idx_min_plays, "Period"]
        period_min_plays_val = summary_full.loc[idx_min_plays, "Plays"]

        avg_plays = round(summary_full["Plays"].mean(), 2)

        # --------------------------
        # Top Artist / Track / Album usando summary_full
        # --------------------------
        # Agrupamos por Artist / Track / Album sobre df_filtered ya resumido por periodo
        top_artist_series = summary_full.groupby("Top Artist").size()
        top_artist = top_artist_series.idxmax()
        top_artist_count = top_artist_series.max()

        top_track_series = summary_full.groupby("Top Track").size()
        top_track = top_track_series.idxmax()
        top_track_count = top_track_series.max()

        top_album_series = summary_full.groupby("Top Album").size()
        top_album = top_album_series.idxmax()
        top_album_count = top_album_series.max()
        
        # Genre
        if "Top Genre" in summary_full.columns:
            top_genre_series = summary_full.groupby("Top Genre").size()
            top_genre = top_genre_series.idxmax()
            top_genre_count = top_genre_series.max()
        else:
            top_genre, top_genre_count = None, 0

        top_decade_series = summary_full.groupby("Top Decade").size()
        top_decade = top_decade_series.idxmax()
        top_decade_count = top_decade_series.max()

        # --------------------------
        # Rachas consecutivas
        # --------------------------
        summary_sorted = summary_full.sort_values("Period")

        track_streak_val, track_streak_len = longest_streak(summary_sorted["Top Track"])
        artist_streak_val, artist_streak_len = longest_streak(summary_sorted["Top Artist"])
        album_streak_val, album_streak_len = longest_streak(summary_sorted["Top Album"])
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

        # --------------------------
        # Mostrar métricas
        # --------------------------
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

        r2.metric(
            "Longest Top Artist streak",
            f"{artist_streak_val} ({artist_streak_len})",
            help=f"{artist_streak_val} ({artist_streak_len})")
        r1.metric(
            "Longest Top Track streak",
            f"{track_streak_val} ({track_streak_len})",
            help=f"{track_streak_val} ({track_streak_len})")
        r3.metric(
            "Longest Top Album streak",
            f"{album_streak_val} ({album_streak_len})",
            help=f"{album_streak_val} ({album_streak_len})")
        r4.metric(
            "Longest Top Genre streak",
            f"{genre_streak_val} ({genre_streak_len})",
            help=f"{genre_streak_val} ({genre_streak_len})")
        r5.metric(
            "Longest Top Decade streak",
            f"{decade_streak_val} ({decade_streak_len})",
            help=f"{decade_streak_val} ({decade_streak_len})")

        r1, r2, r3, r4, r5 = st.columns(5)

        r1.metric("New artists discovered", len(new_artists))
        r2.metric("New tracks discovered", len(new_tracks))
        r3.metric("New albums discovered", len(new_albums))
        r4.metric("New genres discovered", len(new_genres))
        r5.metric("New decades discovered", len(new_decades))

        st.metric("Artist diversity index", round(diversity,3))
        

    # --------------------------
    # Tabla en orden descendente
    # --------------------------
    summary_table = summary_full.sort_values("Period", ascending=False).head(global_rows_to_show)
    rows = len(summary_table)
    calculated_height = (rows + 1) * 35 + 3
    st.dataframe(summary_table,hide_index=True,use_container_width=True,height=calculated_height)
    
    # =========================
    # Tablas de descubrimientos
    # =========================

    st.markdown("## New Discoveries")

    # ---------------- Artists ----------------
    if len(new_artists) > 0:
        artists_table = format_first_listen_table(new_artists, "artist")
        artists_table = artists_table.head(global_rows_to_show)
        
        st.markdown("### 🎤 New Artists")
        rows = len(artists_table)
        calculated_height = (rows + 1) * 35 + 3
        st.dataframe(artists_table,hide_index=True,use_container_width=True,height=calculated_height)
        
    # ---------------- Tracks ----------------
    if len(new_tracks) > 0:
        tracks_table = format_first_listen_table(new_tracks, "track")
        tracks_table = tracks_table.head(global_rows_to_show)
        
        st.markdown("### 🎵 New Tracks")
        rows = len(tracks_table)
        calculated_height = (rows + 1) * 35 + 3
        st.dataframe(tracks_table, hide_index=True, use_container_width=True, height=calculated_height)

    # ---------------- Albums ----------------
    if len(new_albums) > 0:
        albums_table = format_first_listen_table(new_albums, "album_clean")
        albums_table = albums_table.head(global_rows_to_show)
        
        st.markdown("### 💿 New Albums")
        rows = len(albums_table)
        calculated_height = (rows + 1) * 35 + 3
        st.dataframe(albums_table, hide_index=True, use_container_width=True, height=calculated_height)

    # ---------------- Genres ----------------
    if len(new_genres) > 0:
        genres_table = format_first_listen_table(new_genres, "genre_single")
        genres_table = genres_table.head(global_rows_to_show)
        
        st.markdown("### 🎼 New Genres")
        rows = len(genres_table)
        calculated_height = (rows + 1) * 35 + 3
        st.dataframe(genres_table, hide_index=True, use_container_width=True, height=calculated_height)

    # ---------------- Decades ----------------
    if len(new_decades) > 0:
        decades_table = new_decades.copy()

        decades_table["first_listen"] = decades_table["first_listen"].dt.tz_convert(LOCAL_TZ)

        # Orden correcto
        decades_table = decades_table.sort_values("first_listen", ascending=True)

        decades_table["First Listen"] = decades_table["first_listen"] \
            .dt.strftime("%d/%m/%Y %H:%M:%S")

        decades_table = decades_table[["decade", "First Listen"]] \
            .head(global_rows_to_show)

        st.markdown("### 🗓️ New Decades")
        st.dataframe(decades_table, hide_index=True)
    # --------------------------
    # Gráficas de minutos y plays
    # --------------------------

    # Asegúrate de que Period sea tipo fecha si corresponde
    # summary_full["Period"] = pd.to_datetime(summary_full["Period"])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Serie 1: Minutes (eje Y primario)
    fig.add_trace(
        go.Scatter(
            x=summary_full["Period"],
            y=summary_full["Minutes"],
            mode="lines+markers",
            name="Minutes",
            line=dict(color="#1f77b4")
        ),
        secondary_y=False
    )

    # Serie 2: Plays (eje Y secundario)
    fig.add_trace(
        go.Scatter(
            x=summary_full["Period"],
            y=summary_full["Plays"],
            mode="lines+markers",
            name="Plays",
            line=dict(color="#ff7f0e")
        ),
        secondary_y=True
    )

    fig.update_layout(
        title_text="Minutos y Reproducciones en el Tiempo",
        legend_title_text="Métrica",
    )

    fig.update_xaxes(title_text="Fecha")
    fig.update_yaxes(title_text="Minutes", secondary_y=False)
    fig.update_yaxes(title_text="Plays", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


# =========================
# TAB 2 - Full Data Viewer
# =========================

with tab2:

    # --------------------------------------------------
    # Filtrado por fecha y turno
    # --------------------------------------------------
    df_fd = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_fd = apply_time_filter(df_fd, global_time_filter).copy()

    df_fd["track"] = df_fd["track"].astype(str).str.title().str.strip()
    df_fd["artist"] = df_fd["artist"].astype(str).str.title().str.strip()
    if "album" in df_fd.columns:
        df_fd["album"] = df_fd["album"].astype(str).str.title().str.strip()

    df_fd["decade"] = df_fd["year_release"].apply(get_decade)
    df_fd_dec = df_fd[df_fd["decade"].notna()]

    # --------------------------------------------------
    # Días efectivos
    # --------------------------------------------------
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

    # =========================
    # TRACKS
    # =========================
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
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'), help=first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'), help=last_play.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        c1.metric("Longest track repeat streak", "-")
        c2.metric("First play of the streak", "-")
        c3.metric("Last play of the streak", "-")

    # Racha por minutos
    mt1, mt2, mt3 = st.columns(3)
    track_val_m, track_minutes, first_m, last_m = longest_consecutive_block_minutes(df_fd, "track")
    if track_val_m:
        mt1.metric("Longest track minutes streak", f"{track_minutes:.2f} min of {track_val_m}", help=f"{track_minutes:.2f} min of {track_val_m}")
        mt2.metric("First play of the minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'), help=first_m.strftime('%Y-%m-%d %H:%M:%S'))
        mt3.metric("Last play of the minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'), help=last_m.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        mt1.metric("Longest track minutes streak", "-")
        mt2.metric("First play of the minutes streak", "-")
        mt3.metric("Last play of the minutes streak", "-")

    # Summary y artista principal
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
    calculated_height = (len(tracks_summary) + 1) * 35 + 3
    st.dataframe(tracks_summary, hide_index=True, use_container_width=True,height=calculated_height)

    # =========================
    # ARTISTS
    # =========================
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
    # Usamos df con el mismo title-case que df_fd para que el merge no falle por casing
    _df_afl = df.copy()
    _df_afl["artist"] = _df_afl["artist"].astype(str).str.title().str.strip()
    artist_first_listen = _df_afl.groupby("artist")["datetime"].min().reset_index()
    artist_first_listen["First Listen"] = artist_first_listen["datetime"].dt.tz_convert(LOCAL_TZ).dt.strftime("%d/%m/%Y %H:%M:%S")
    artists_summary = artists_summary.merge(artist_first_listen, left_on="Artist", right_on="artist", how="left")
    artists_summary = artists_summary[["Artist", "First Listen", "Minutes", "Minutes%", "Plays", "Plays%"]].head(global_rows_to_show)
    calculated_height = (len(artists_summary) + 1) * 35 + 3
    st.dataframe(artists_summary, hide_index=True, use_container_width=True, height=calculated_height)

    ## =========================
    # ALBUMS (CORREGIDO PARA USAR LA COLUMNA LIMPIA)
    # =========================
    st.markdown("### Albums")
    # Usamos album_clean para contar únicos
    n_unique_albums = df_fd["album_clean"].nunique() 
    avg_minutes_per_album = round(total_minutes_fd / n_unique_albums, 2) if n_unique_albums else 0.0

    c1, c2, c4, c3 = st.columns(4)
    c1.metric("Unique albums", n_unique_albums)
    c2.metric("Minutes per album", f"{avg_minutes_per_album:.2f} min")
    c3.metric("Plays per day", plays_per_day)
    c4.metric("Minutes per day", f"{minutes_per_day:.2f} min")

    # Rachas usando la columna limpia
    top_album_val, top_album_size, first_play, last_play = longest_consecutive_block_details(df_fd, "album_clean")
    c1, c2, c3 = st.columns(3)
    if top_album_val:
        c1.metric("Longest album repeat streak", f"{top_album_size} plays of {top_album_val}")
        c2.metric("First play of the streak", first_play.strftime('%Y-%m-%d %H:%M:%S'))
        c3.metric("Last play of the streak", last_play.strftime('%Y-%m-%d %H:%M:%S'))

    # Rachas por minutos usando la columna limpia
    mal1, mal2, mal3 = st.columns(3)
    album_val_m, album_minutes, first_m, last_m = longest_consecutive_block_minutes(df_fd, "album_clean")
    if album_val_m:
        mal1.metric("Longest album minutes streak", f"{album_minutes:.2f} min of {album_val_m}")
        mal2.metric("First play of the minutes streak", first_m.strftime('%Y-%m-%d %H:%M:%S'))
        mal3.metric("Last play of the minutes streak", last_m.strftime('%Y-%m-%d %H:%M:%S'))

    # TABLA DE RESUMEN: Aquí es donde se agrupaba mal
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
    
    calculated_height = (len(albums_summary) + 1) * 35 + 3
    st.dataframe(albums_summary, hide_index=True, use_container_width=True, height=calculated_height)

    # =========================
    # GENRES
    # =========================
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

    # Rachas por primary genre
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
        longest_streak = genre_plays[genre_plays["streak_id"] == streak_lengths.idxmax()]

        first_play = longest_streak["datetime"].min()
        last_play = longest_streak["datetime"].max()
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

    # Tabla de géneros
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

    # =========================
    # DECADES
    # =========================
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
    
# =========================
# TAB 3 - Time Patterns
# =========================

with tab3:

    # =========================
    # CLOCK CHART — Listening Time by Hour (Radial)
    # =========================
    df_clock = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_clock = apply_time_filter(df_clock, global_time_filter).copy()

    if not df_clock.empty:
        df_clock["hour"] = df_clock["datetime"].dt.hour

        summary_clock = (
            df_clock.groupby("hour")["duration"].sum().reset_index()
        )
        summary_clock["minutes"] = summary_clock["duration"] / 60

        # Convertimos horas a strings para poder ordenarlas correctamente en polar
        summary_clock["hour_str"] = summary_clock["hour"].astype(str)

        # Orden de horas circular 0–23
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

        # Estética coherente con la app
        fig_clock.update_traces(
            line=dict(color="#FF4B4B", width=3),
            marker=dict(size=6, color="#FF4B4B")
        )

        # Ajustes de eje polar estilo reloj
        fig_clock.update_layout(
            polar=dict(
                bgcolor="#111825",   
                radialaxis=dict(
                            showticklabels=False,   # Oculta los números
                            ticks='',               # Quita marcas
                            showgrid=True,          # Mantiene la rejilla (opcional)
                            gridcolor="#3a4750",
                            showline=False,          # Sin línea radial central
                        ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,        # 0h hacia arriba
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

    # =========================
    # HEATMAP 1 — Hora (filas) × Día de la semana (columnas)
    # =========================
    df_hm = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_hm = apply_time_filter(df_hm, global_time_filter).copy()

    df_hm["hour"] = df_hm["datetime"].dt.hour
    df_hm["weekday"] = df_hm["datetime"].dt.day_name()

    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    heatmap1 = (
        df_hm.groupby(["hour", "weekday"])["duration"].sum()
        .reset_index()
        .pivot(index="hour", columns="weekday", values="duration")
        .reindex(columns=weekday_order, fill_value=0)
    ) / 60
    heatmap1 = heatmap1.round(2)

    fig_hm1 = px.imshow(
        heatmap1.values,                    # pasar solo los valores
        x=heatmap1.columns,                 # columnas = weekdays
        y=heatmap1.index,                   # filas = hours
        labels=dict(x="Weekday", y="Hour", color="Minutes"),
        title="Heatmap — Minutes by Hour × Weekday",
        color_continuous_scale=[
            "#0d1b2a", "#3b1c5a", "#b52a3a", "#ff6e48", "#ffe04b"
        ],
        zmin=0,                             # asegura que el mínimo sea 0
        zmax=heatmap1.values.max(),         # máximo de la matriz
        aspect="auto"
    )
    fig_hm1.update_xaxes(side="top")
    st.plotly_chart(fig_hm1, use_container_width=True)


    # =========================
    # HEATMAP 2 — Día (filas) × Mes (columnas)
    # =========================
    df_hm2 = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_hm2 = apply_time_filter(df_hm2, global_time_filter).copy()

    df_hm2["weekday"] = df_hm2["datetime"].dt.day_name()
    df_hm2["month"] = df_hm2["datetime"].dt.strftime("%Y-%m")

    heatmap2 = (
        df_hm2.groupby(["weekday", "month"])["duration"].sum()
        .reset_index()
        .pivot(index="weekday", columns="month", values="duration")
        .reindex(index=weekday_order, fill_value=0)
    ) / 60
    heatmap2 = heatmap2.round(2)

    fig_hm2 = px.imshow(
        heatmap2.values,
        x=heatmap2.columns,
        y=heatmap2.index,
        labels=dict(x="Month", y="Weekday", color="Minutes"),
        title="Heatmap — Minutes by Weekday × Month",
        color_continuous_scale=[
            "#0d1b2a", "#3b1c5a", "#b52a3a", "#ff6e48", "#ffe04b"
        ],
        zmin=0,
        zmax=heatmap2.values.max(),
        aspect="auto"
    )
    fig_hm2.update_xaxes(side="top")
    st.plotly_chart(fig_hm2, use_container_width=True)

with tab4:

    # ---------- Helpers de construcción de "Period" y figura ----------
    def add_period_column(df_in: pd.DataFrame, period: str, tz_name: str) -> pd.DataFrame:
        """Crea la columna 'Period' coherente con get_listening_summary (day/week/month/year)."""
        df_out = df_in.copy()
        if df_out.empty:
            df_out["Period"] = pd.NaT
            return df_out

        if period == "week":
            df_out["Period"] = (
                df_out["datetime"]
                .dt.tz_convert(tz_name)
                .dt.to_period("W")
                .apply(lambda r: r.start_time.date())
            )
        elif period == "day":
            df_out["Period"] = df_out["datetime"].dt.tz_convert(tz_name).dt.date
        elif period == "month":
            df_out["Period"] = (
                df_out["datetime"]
                .dt.tz_convert(tz_name)
                .dt.to_period("M")
                .apply(lambda r: r.start_time.date())
            )
        elif period == "year":
            df_out["Period"] = (
                df_out["datetime"]
                .dt.tz_convert(tz_name)
                .dt.to_period("Y")
                .apply(lambda r: r.start_time.date())
            )
        else:
            df_out["Period"] = (
                df_out["datetime"]
                .dt.tz_convert(tz_name)
                .dt.to_period("M")
                .apply(lambda r: r.start_time.date())
            )
        return df_out

    def build_evolution_figure(summary_df: pd.DataFrame, top_labels: list, label_col: str, title: str, x_title: str):
        """Crea un gráfico líneas+marcadores de evolución por 'Period' para los labels indicados."""
        fig = go.Figure()
        colors = px.colors.qualitative.Safe
        # asegurar orden temporal
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

    df_sorted = df_filtered.sort_values("datetime")

    df_sorted["gap"] = df_sorted["datetime"].diff().dt.total_seconds() / 60

    df_sorted["session"] = (df_sorted["gap"] > 30).cumsum()

    sessions = df_sorted.groupby("session").agg(
        start=("datetime", "min"),
        end=("datetime", "max"),        # timestamp de inicio del último track
        last_duration=("duration", "last"),   # duración del último track
        plays=("track","count"),
        minutes_total=("duration", "sum")    # minutos totales de la sesión
    )

    sessions["minutes_total"] = sessions["minutes_total"] / 60
    # end real = timestamp inicio último track + duración del track
    sessions["end"] = sessions["end"] + pd.to_timedelta(sessions["last_duration"], unit='s')

    sessions["length"] = (sessions["end"] - sessions["start"]).dt.total_seconds() / 60
    sessions["%listening"] = (sessions["minutes_total"] / sessions["length"])*100

    longest_session = sessions.loc[sessions["length"].idxmax()]

    sessions_to_show = sessions.drop(columns=["last_duration"])

    st.dataframe(sessions_to_show.reset_index(drop=True).sort_values("length", ascending=False).head(global_rows_to_show), hide_index=True, use_container_width=True, height=(len(sessions_to_show.head(global_rows_to_show)) + 1) * 35 + 3)
    # =========================
    # Track Listening Evolution — afecta a TODOS los filtros globales
    # =========================

    # 1) Filtrar por rango y franja
    df_track_ev = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_track_ev = apply_time_filter(df_track_ev, global_time_filter).copy()

    if not df_track_ev.empty:
        # 2) Period según global_period
        df_track_ev = add_period_column(df_track_ev, global_period, LOCAL_TZ)
                
        top_tracks = (
            df_track_ev.groupby("track")["duration"]
            .sum()
            .sort_values(ascending=False)
            .head(global_top_n)
            .index
        )

        df_track_ev = df_track_ev[df_track_ev["track"].isin(top_tracks)].copy()

        # 4) Resumen de minutos por track y Period
        summary_tracks = (
            df_track_ev.groupby(["Period", "track"])["duration"]
            .sum()
            .reset_index()
            .rename(columns={"track": "Track"})
        )
        summary_tracks["Minutes"] = summary_tracks["duration"] / 60.0

        # 5) Construir figura
        x_title = {"day":"Day","week":"Week (start date)","month":"Month","year":"Year"}.get(global_period, "Period")
        fig_tracks = build_evolution_figure(summary_tracks, list(top_tracks), "Track",
                                            f"Track Listening Evolution — grouped by {global_period}",
                                            x_title)
        st.plotly_chart(fig_tracks, use_container_width=True)
    else:
        st.info("No hay datos de tracks para el rango/periodo/turno seleccionados.")

    # =========================
    # Artist Listening Evolution — afecta a TODOS los filtros globales
    # =========================

    # 1) Filtrar por rango y franja
    df_artist_ev = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_artist_ev = apply_time_filter(df_artist_ev, global_time_filter).copy()

    if not df_artist_ev.empty:
        # 2) Period según global_period
        df_artist_ev = add_period_column(df_artist_ev, global_period, LOCAL_TZ)
        
        top_artists = (
            df_artist_ev.groupby("artist")["duration"]
            .sum()
            .sort_values(ascending=False)
            .head(global_top_n)
            .index
        )

        df_artist_ev = df_artist_ev[df_artist_ev["artist"].isin(top_artists)].copy()

        # 4) Resumen de minutos por artista y Period
        summary_artists = (
            df_artist_ev.groupby(["Period", "artist"])["duration"]
            .sum()
            .reset_index()
            .rename(columns={"artist": "Artist"})
        )
        summary_artists["Minutes"] = summary_artists["duration"] / 60.0

        # 5) Construir figura con helper
        x_title = {"day":"Day","week":"Week (start date)","month":"Month","year":"Year"}.get(global_period, "Period")
        fig_artists = build_evolution_figure(
            summary_df=summary_artists,
            top_labels=list(top_artists),
            label_col="Artist",
            title=f"Artist Listening Evolution — grouped by {global_period}",
            x_title=x_title
        )

        st.plotly_chart(fig_artists, use_container_width=True)
    else:
        st.info("No hay datos de artistas para el rango/periodo/turno seleccionados.")


    # =========================
    # Album Listening Evolution — afecta a TODOS los filtros globales
    # =========================

    df_album_ev = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_album_ev = apply_time_filter(df_album_ev, global_time_filter).copy()

    # Si 'album' puede ser NaN, limpiamos
    df_album_ev = df_album_ev[df_album_ev["album"].notna()]

    if not df_album_ev.empty:
        df_album_ev = add_period_column(df_album_ev, global_period, LOCAL_TZ)

        top_albums = (
            df_album_ev.groupby("album")["duration"]
            .sum()
            .sort_values(ascending=False)
            .head(global_top_n)
            .index
        )
        df_album_ev = df_album_ev[df_album_ev["album"].isin(top_albums)].copy()

        summary_albums = (
            df_album_ev.groupby(["Period", "album"])["duration"]
            .sum()
            .reset_index()
            .rename(columns={"album": "Album"})
        )
        summary_albums["Minutes"] = summary_albums["duration"] / 60.0

        x_title = {"day":"Day","week":"Week (start date)","month":"Month","year":"Year"}.get(global_period, "Period")
        fig_albums = build_evolution_figure(summary_albums, list(top_albums), "Album",
                                            f"Album Listening Evolution — grouped by {global_period}",
                                            x_title)
        st.plotly_chart(fig_albums, use_container_width=True)
    else:
        st.info("No hay datos de álbumes para el rango/periodo/turno seleccionados.")


    # =========================
    # Genre Listening Evolution — crédito completo y TODOS los filtros globales
    # =========================

    df_gen_ev = df_genre[(df_genre["datetime"] >= global_start) & (df_genre["datetime"] <= global_end)]
    df_gen_ev = apply_time_filter(df_gen_ev, global_time_filter).copy()

    # Limpiar NAs por seguridad
    df_gen_ev = df_gen_ev[df_gen_ev["genre_single"].notna()]

    if not df_gen_ev.empty:
        df_gen_ev = add_period_column(df_gen_ev, global_period, LOCAL_TZ)

        top_genres = (
            df_gen_ev.groupby("genre_single")["duration"]
            .sum()
            .sort_values(ascending=False)
            .head(global_top_n)
            .index
        )
        df_gen_ev = df_gen_ev[df_gen_ev["genre_single"].isin(top_genres)].copy()

        summary_genres = (
            df_gen_ev.groupby(["Period", "genre_single"])["duration"]
            .sum()
            .reset_index()
            .rename(columns={"genre_single": "Genre"})
        )
        summary_genres["Minutes"] = summary_genres["duration"] / 60.0

        x_title = {"day":"Day","week":"Week (start date)","month":"Month","year":"Year"}.get(global_period, "Period")
        fig_genres = build_evolution_figure(summary_genres, list(top_genres), "Genre",
                                            f"Genre Listening Evolution — grouped by {global_period}",
                                            x_title)
        st.plotly_chart(fig_genres, use_container_width=True)
    else:
        st.info("No hay datos de géneros para el rango/periodo/turno seleccionados.")





    df_month = df_filtered.copy()
    df_month["month"] = df_month["datetime"].dt.to_period("M")

    dominant = (
        df_month.groupby(["month","artist"])["duration"]
        .sum()
        .reset_index()
    )

    idx = dominant.groupby("month")["duration"].idxmax()

    dominant = dominant.loc[idx]
    dominant["minutes"] = dominant["duration"]/60

with tab5:
    st.header("Music Search / Filter")

    # --- INPUTS DE FILTRO ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        track_input = st.text_input("Track contains")
        artist_input = st.text_input("Artist contains")
    
    with col2:
        album_input = st.text_input("Album contains")
    
    with col3:
        duration_range = st.slider(
            "Duration (seconds)",
            min_value=0,
            max_value=int(df["duration"].max()) if not df.empty else 600,
            value=(0, int(df["duration"].max()) if not df.empty else 600)
        )
    
    year_filter = st.slider(
        "Release year",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
    )

    # --- FILTRAR DATAFRAME ---
    df_search = df.copy()
    
    if track_input:
        df_search = df_search[df_search["track"].str.contains(track_input, case=False, na=False)]
    if artist_input:
        df_search = df_search[df_search["artist"].str.contains(artist_input, case=False, na=False)]
    if album_input:
        df_search = df_search[df_search["album"].str.contains(album_input, case=False, na=False)]
    
    df_search = df_search[
        (df_search["duration"].between(duration_range[0], duration_range[1])) &
        (df_search["year_release"].between(year_filter[0], year_filter[1]))
    ]

    # --- AGREGAR RESUMEN POR TRACK ---
    if not df_search.empty:
        summary_search = (
            df_search.groupby(["track","artist","album"])
            .agg(
                Plays=("track", "count"),
                Minutes=("duration", lambda x: round(x.sum()/60, 2)),
                Year=("year_release", "first"),
                Duration=("duration", "first")
            )
            .reset_index()
            .sort_values("Minutes", ascending=False)
        )
    else:
        summary_search = pd.DataFrame(columns=["track","artist","album","Plays","Minutes","Year","Duration"])

    display_aggrid(summary_search, container_id="search_tab_grid")

# =========================
# TAB 6 - HEATMAP HORA vs DÍA
# =========================
with tab6:
    st.header("Hourly / Weekday Heatmap")
    df_ht = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_ht = apply_time_filter(df_ht, global_time_filter)
    if df_ht.empty:
        st.info("No data for selected range/filter")
    else:
        df_ht = df_ht.copy()
        df_ht["hour"] = df_ht["datetime"].dt.hour
        df_ht["weekday"] = df_ht["datetime"].dt.day_name()
        order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        df_ht["weekday"] = pd.Categorical(df_ht["weekday"], categories=order, ordered=True)
        # usar density_heatmap para control de colores
        df_ht["duration_min"] = df_ht["duration"] / 60.0
        fig = px.density_heatmap(
            df_ht,
            x="hour",
            y="weekday",
            z="duration_min",
            histfunc="sum",
            labels={"hour":"Hour","weekday":"Weekday","z":"Minutes"},
            color_continuous_scale="Viridis",
            nbinsx=24,
            nbinsy=7
        )
        fig.update_traces(zmax=df_ht["duration_min"].sum())  # forzar escala completa
        st.plotly_chart(fig, use_container_width=True)

# =========================
# TAB 7 - WORDCLOUD REAL
# =========================
with tab7:
    st.header("Wordcloud of track titles & artists")
    if not _HAS_WORDCLOUD:
        st.error("wordcloud package not installed. Install via `pip install wordcloud` or use requirements file.")
    df_wc = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_wc = apply_time_filter(df_wc, global_time_filter)
    if df_wc.empty:
        st.info("No data for selected range/filter")
    else:
        text = " ".join(
            df_wc["track"].astype(str).tolist() + df_wc["artist"].astype(str).tolist()
        )
        words = re.findall(r"\w+", text.lower())
        if words:
            if _HAS_WORDCLOUD:
                wc = WordCloud(width=800, height=400, background_color="white").generate(" ".join(words))
                st.image(wc.to_array(), use_column_width=True)
            else:
                counts = pd.Series(words).value_counts().head(50).reset_index()
                counts.columns = ["word","count"]
                fig = px.bar(
                    counts,
                    x="word",
                    y="count",
                    title="Most common words (bar chart fallback)",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No words found in the selection")

# =========================
# TAB 8 - SIMPLE PREDICTION
# =========================
with tab8:
    st.header("Trend & Forecast")
    df_pf = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_pf = apply_time_filter(df_pf, global_time_filter)
    summary_pred = get_listening_summary(df_pf, global_period)
    if summary_pred.empty:
        st.info("No data to predict")
    else:
        summary_pred = summary_pred.copy()
        # convertir Period a datetime para ordenar
        summary_pred["PeriodDt"] = pd.to_datetime(summary_pred["Period"])
        summary_pred = summary_pred.sort_values("PeriodDt")
        X = np.arange(len(summary_pred)).reshape(-1,1)
        y = summary_pred["Minutes"].values
        model = LinearRegression()
        model.fit(X, y)
        forecast_horizon = 3
        forecast_idx = np.arange(len(summary_pred), len(summary_pred)+forecast_horizon).reshape(-1,1)
        preds = model.predict(forecast_idx)
        # generar fechas futuras según global_period
        freq_map = {"day":"D","week":"W","month":"M","year":"Y"}
        last_date = summary_pred["PeriodDt"].iloc[-1]
        future_dates = pd.date_range(start=last_date + pd.offsets.DateOffset(1), periods=forecast_horizon, freq=freq_map.get(global_period, "M"))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=summary_pred["PeriodDt"], y=y, mode="lines+markers", name="Actual"))
        fig.add_trace(go.Scatter(x=future_dates, y=preds, mode="lines+markers", name="Forecast"))
        fig.update_layout(title="Minutes trend and short-term forecast")
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"Equation: minutes = {model.coef_[0]:.2f} * period + {model.intercept_:.2f}, R² = {model.score(X,y):.3f}")

# =========================
# TAB 9 - GENRE CO-OCCURRENCE
# =========================
with tab9:
    st.header("Genre co-occurrence heatmap")
    df_n = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_n = apply_time_filter(df_n, global_time_filter)
    if df_n.empty:
        st.info("No data for selected range/filter")
    else:
        df_n = df_n.copy()
        df_n["genres_list"] = df_n["genre"].apply(split_genres).apply(lambda lst: [normalize_genre_name(g) for g in lst if g])
        from itertools import combinations
        pairs = {}
        for gl in df_n["genres_list"]:
            unique = sorted(set(gl))
            for a,b in combinations(unique,2):
                pairs[(a,b)] = pairs.get((a,b),0) + 1
        if not pairs:
            st.info("No multi-genre tracks to compute co-occurrence")
        else:
            genres = sorted({g for pair in pairs for g in pair})
            mat = pd.DataFrame(0, index=genres, columns=genres)
            for (a,b),cnt in pairs.items():
                mat.loc[a,b] = cnt
                mat.loc[b,a] = cnt
            fig = px.imshow(mat, labels={"x":"Genre","y":"Genre","color":"Count"}, color_continuous_scale="Inferno")
            st.plotly_chart(fig, use_container_width=True)

# =========================
# TAB 10 - DIVERSITY OVER TIME
# =========================
with tab10:
    st.header("Artist diversity per period (Shannon index)")
    df_div = df[(df["datetime"] >= global_start) & (df["datetime"] <= global_end)]
    df_div = apply_time_filter(df_div, global_time_filter)
    if df_div.empty:
        st.info("No data")
    else:
        temp = df_div.copy()
        if global_period == "week":
            temp["Period"] = temp["datetime"].dt.to_period("W").apply(lambda r: r.start_time.date())
        elif global_period == "day":
            temp["Period"] = temp["datetime"].dt.date
        elif global_period == "month":
            temp["Period"] = temp["datetime"].dt.to_period("M").apply(lambda r: r.start_time.date())
        elif global_period == "year":
            temp["Period"] = temp["datetime"].dt.to_period("Y").apply(lambda r: r.start_time.date())
        counts = temp.groupby(["Period","artist"]).size()
        # convertir a proporciones por periodo
        prop = counts.groupby(level=0).apply(lambda s: s / s.sum())
        shannon = prop.groupby(level=0).apply(lambda s: -(s * np.log(s)).sum())
        sh_df = shannon.reset_index(name="Shannon")
        # ordenar por fecha si posible
        try:
            sh_df["PeriodDt"] = pd.to_datetime(sh_df["Period"])
            sh_df = sh_df.sort_values("PeriodDt")
        except Exception:
            pass
        fig = px.line(sh_df, x="Period", y="Shannon", title="Artist diversity (Shannon index)")
        st.plotly_chart(fig, use_container_width=True)