import pandas as pd
import os
import re
from datetime import datetime
import streamlit as st
from utils.helpers import _parse_year_mixed, _sanitize_year, split_genres, normalize_genre_name, LOCAL_TZ, get_decade

DATA_PATH = "data/aleex_cs.csv"
DURATIONS_PATH = "data/musica.csv"

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
    if not isinstance(track, str):
        return False
    if _YT_JUNK_RE.search(track):
        return True
    if isinstance(artist, str) and artist:
        artist_norm = artist.lower().strip()
        track_norm  = track.lower().strip()
        if track_norm.startswith(artist_norm + " - ") or track_norm.startswith(artist_norm + "- "):
            return True
    return False

@st.cache_data
def load_data():
    import io as _io
    raw_content = None

    if not os.path.exists(DATA_PATH):
        st.info("👋 ¡Bienvenido! No hemos encontrado tu historial localmente.")
        uploaded_file = st.file_uploader("Sube tu archivo aleex_cs.csv para empezar", type=["csv"])
        if uploaded_file is not None:
            raw_content = uploaded_file.getvalue().decode("utf-8-sig", errors="replace")
        else:
            st.stop()
    else:
        with open(DATA_PATH, "r", encoding="utf-8-sig", errors="replace") as _f:
            raw_content = _f.read()

    try:
        raw_lines = raw_content.splitlines()
        clean_lines = [raw_lines[0]]
        for _line in raw_lines[1:]:
            _s = _line.strip()
            # Limpieza agresiva: quitar comillas externas y des-escapar internas
            if _s.startswith('"') and _s.endswith('"'):
                _s = _s[1:-1].replace('""', '"')
            clean_lines.append(_s + "\n")

        # Usamos engine='python' y sep=',' explícito para evitar fallos de detección
        scrobbles = pd.read_csv(_io.StringIO("".join(clean_lines)), sep=",", on_bad_lines="skip", engine='python')
    except Exception as e:
        st.error(f"Error parseando el CSV: {e}")
        return pd.DataFrame()

    scrobbles.columns = scrobbles.columns.str.strip()

    if 'uts' in scrobbles.columns:
        scrobbles['uts'] = pd.to_numeric(scrobbles['uts'], errors='coerce')
        scrobbles = scrobbles.dropna(subset=['uts'])
        scrobbles["datetime"] = pd.to_datetime(scrobbles["uts"], unit="s", utc=True).dt.tz_convert(LOCAL_TZ)
    elif 'date' in scrobbles.columns:
        scrobbles["datetime"] = pd.to_datetime(scrobbles["date"])
    else:
        date_col = next((c for c in scrobbles.columns if 'date' in c.lower() or 'time' in c.lower()), None)
        if date_col:
            scrobbles["datetime"] = pd.to_datetime(scrobbles[date_col], errors='coerce')
        else:
            scrobbles["datetime"] = pd.to_datetime(scrobbles.iloc[:, 0], errors='coerce')

    equivalencias = pd.DataFrame({
        "original": [
            "Smash (ESP)", "Smash", "Jim Morrison", "Robe.", "I Nomadi",
            "Godspeed You Black Emperor!", "Fito Y Fitipaldis", "Fabrizio de Andre'",
            "Fabrizio De Andre", "Fabrizio De AndrÃ©", "Fabrizio De André",
            "Mark Knopfler & Emmylou Harris", "TheKnackVEVO", "joaquinsabinaVEVO",
            "ZoeVEVO", "calle13vevo", "ojetecalormusica", "fito&fitipaldisVEVO",
            "Fabrizio De AndrÃ¨", "Guns N' Roses",
            "The Tonight Show starring Jimmy Fallon", "The Game Awards",
            "FrancodeVitaVEVO", "CoezVEVO", "FrancescoGucciniVEVO",
            "Lorenzo Jovanotti Cherubini",
            "Canal Nostalgia", "Date un Vlog", "Mensaje de Voz",
            "Nacional Records", "Warner Music Spain", "Waves Consumer Electronics",
            "Hank Mc Koy",
        ],
        "canonico": [
            "Smash", "Smash", "The Doors", "Robe", "Nomadi",
            "Godspeed You! Black Emperor", "Fito & Fitipaldis", "Fabrizio De Andre'",
            "Fabrizio De Andre'", "Fabrizio De Andre'", "Fabrizio De Andre'",
            "Mark Knopfler", "The Knack", "Joaquín Sabina",
            "Zoe", "Calle 13", "Ojete Calor", "Fito & Fitipaldis",
            "Fabrizio De Andre'", "Guns N' Roses",
            "Jimmy Fallon", "Various Artists",
            "Franco De Vita", "Coez", "Francesco Guccini",
            "Jovanotti",
            "_NON_MUSIC_", "_NON_MUSIC_", "_NON_MUSIC_",
            "_NON_MUSIC_", "_NON_MUSIC_", "_NON_MUSIC_",
            "_NON_MUSIC_",
        ]
    })
    for i, row in equivalencias.iterrows():
        scrobbles["artist"] = scrobbles["artist"].replace(row["original"], row["canonico"])
    scrobbles["artist"] = scrobbles["artist"].astype(str).str.replace(r" - .*", "", regex=True)

    durations = pd.DataFrame()
    if os.path.exists(DURATIONS_PATH):
        try:
            durations = pd.read_csv(DURATIONS_PATH, sep=None, engine='python', encoding='utf-8-sig')
            durations.columns = durations.columns.str.strip()
            
            rename_map = {
                "Artista": "artist", "Título": "track", "Género": "genre",
                "Duración(s)": "duration", "Año": "year_raw", "Álbum": "album_musica"
            }
            durations = durations.rename(columns=rename_map)

            if "year_raw" in durations.columns:
                durations["year_release"] = durations["year_raw"].apply(_parse_year_mixed).apply(_sanitize_year)
            
            if "duration" in durations.columns:
                durations["duration"] = pd.to_numeric(durations["duration"], errors="coerce") / 100
        except Exception as e:
            st.warning(f"Error cargando musica.csv: {e}")

    def normalize_str(s):
        return str(s).strip().lower().replace("’", "'") if pd.notna(s) else ""

    scrobbles["artist_norm"] = scrobbles["artist"].apply(normalize_str)
    scrobbles["track_norm"] = scrobbles["track"].apply(normalize_str)
    
    if not durations.empty:
        durations["artist_norm"] = durations["artist"].apply(normalize_str)
        durations["track_norm"] = durations["track"].apply(normalize_str)
        
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

    def normalize_album_full(name):
        if pd.isna(name) or str(name).lower() in ["nan", "unknown album", ""]: return "Unknown Album"
        
        s = str(name)
        # 1. Remove content inside brackets/parens that mentions Discs, CDs, or common junk
        # We use a more aggressive pattern to catch [Disc 2], (Remastered), etc.
        s = re.sub(r'\s*[\(\[].*?(Disc|CD|Remaster|Edition|Maxicut|Deluxe|Live|Explicit|Anniversary|Expanded|Bonus|Digital|Recording|Session|Remastered).*?[\)\]]', '', s, flags=re.IGNORECASE)
        
        # 2. Remove trailing "Disc 1", "CD 1", etc. even without brackets, including those preceded by - or :
        s = re.sub(r'\s+[-:]?\s*(Disc|CD|Vol|Volume|Part|Pt)\s*\d+\s*$', '', s, flags=re.IGNORECASE)
        
        # 3. Trim and collapse whitespace
        clean = " ".join(s.split()).strip()
        
        # 4. Manual overrides for complex cases
        EQUIV = {
            "Ummagumma [Studio Album]": "Ummagumma",
            "Ummagumma [Live Album]": "Ummagumma",
            "The Wall [Disc 1]": "The Wall",
            "The Wall [Disc 2]": "The Wall",
            "Love (Disc 1)": "Love",
            "Love (Disc 2)": "Love"
        }
        return EQUIV.get(clean, clean)

    if "album_musica" in df.columns:
        df["album_clean"] = df["album"].fillna(df["album_musica"]).apply(normalize_album_full)
    else:
        df["album_clean"] = df["album"].apply(normalize_album_full)

    if "genre" not in df.columns: df["genre"] = "Unknown"
    if "year_release" not in df.columns: df["year_release"] = None
    if "duration" not in df.columns: df["duration"] = 0
    
    df = df.drop(columns=["artist_norm", "track_norm"], errors="ignore")
    return df

@st.cache_data
def get_processed_data():
    # Cache buster to ensure album grouping is re-applied: 2026-04-23 12:05
    df = load_data()
    df = df[df["artist"] != "_NON_MUSIC_"].copy()

    df_genre = df.copy()
    df_genre["genre_single"] = df_genre["genre"].fillna("Unknown").apply(split_genres)
    df_genre = df_genre.explode("genre_single")
    df_genre = df_genre.dropna(subset=["genre_single"])
    df_genre["genre_single"] = df_genre["genre_single"].apply(normalize_genre_name)

    df["decade"] = df["year_release"].apply(get_decade)
    df_genre["decade"] = df_genre["year_release"].apply(get_decade)
    
    return df, df_genre
