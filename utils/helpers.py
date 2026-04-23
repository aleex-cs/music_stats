import pandas as pd
import re
import unicodedata
from datetime import datetime, timedelta
import calendar
import pytz

LOCAL_TZ = "Europe/Madrid"

def _parse_year_mixed(cell):
    if pd.isna(cell):
        return None
    s = str(cell).strip()
    if s == "":
        return None

    m = re.fullmatch(r"\s*(\d{4})\s*$", s)
    if m:
        y = int(m.group(1))
        return y

    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="raise")
        return int(dt.year)
    except Exception:
        pass

    m = re.search(r"(\d{4})", s)
    if m:
        y = int(m.group(1))
        return y

    return None

def _sanitize_year(y):
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

def split_genres(cell):
    if pd.isna(cell):
        return []
    parts = re.split(r'[\/,;]', str(cell))
    genres = [p.strip() for p in parts if p and p.strip()]
    return genres

def _strip_accents(text: str) -> str:
    if text is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def normalize_genre_name(g: str) -> str:
    if g is None or str(g).strip() == "":
        return None
    s = str(g).strip()
    s = re.sub(r"\s+", " ", s)
    s = _strip_accents(s)
    s = s.title()

    EQUIV = {
        "Prog Rock": "Progressive Rock",
        "Progressive": "Progressive Rock",
        "Rock Progressif": "Progressive Rock",
        "Progressive Metal": "Progressive Metal",
        "Alt Rock": "Alternative Rock",
        "Alternrock": "Alternative Rock",
        "Alternative": "Alternative Rock",
        "Alternative & Indie": "Indie / Alternative",
        "Alternatif Et Inde": "Indie / Alternative",
        "Indie": "Indie / Alternative",
        "Indie/Alternative": "Indie / Alternative",
        "Indie Alternative": "Indie / Alternative",
        "Psychedelic": "Psychedelic Rock",
        "Acid Rock": "Psychedelic Rock",
        "Roots Rock Blues": "Blues Rock",
        "Rock And Roll": "Rock & Roll",
        "Pop Rock": "Rock Pop", 
        "Contemporary R&B": "R&B",
        "Jazz Funk Soul": "Soul", 
        "Miscellaneous": "Unknown",
        "Art": "Unknown" 
    }

    return EQUIV.get(s, s)

def get_genre_group(genre):
    if pd.isna(genre):
        return "Unknown"
    g = str(genre).lower()
    
    # Metal before Rock because many metal genres contain 'rock' or are subgenres
    if "metal" in g: return "Metal"
    if "punk" in g: return "Punk"
    if "rock" in g: return "Rock"
    if "pop" in g: return "Pop"
    if "jazz" in g: return "Jazz"
    if "blues" in g: return "Blues"
    if "folk" in g: return "Folk"
    if "country" in g: return "Country"
    if "classical" in g: return "Classical"
    if any(x in g for x in ["hip hop", "rap", "trap"]): return "Hip Hop / Rap"
    if any(x in g for x in ["electronic", "techno", "house", "trance", "dance", "synth"]): return "Electronic"
    if "soul" in g or "r&b" in g: return "Soul / R&B"
    if "reggae" in g: return "Reggae"
    if "latin" in g or "salsa" in g or "reggaeton" in g: return "Latin"
    
    return genre.title() if isinstance(genre, str) else "Unknown"

def top_genre_by_minutes_full_credit(group):
    if group.empty or "genre" not in group.columns or "duration" not in group.columns:
        return None

    accum = {}
    for _, row in group.iterrows():
        g_list = split_genres(row.get("genre"))
        dur = row.get("duration")
        if pd.isna(dur) or dur <= 0 or not g_list:
            continue
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

def format_period(p):
    if hasattr(p, "to_timestamp"): # Period object
        if hasattr(p, "freqstr"):
            if "W" in p.freqstr: return f"W{p.week} ({p.start_time.date()})"
            if "M" in p.freqstr: return p.strftime("%b %Y")
            if "A" in p.freqstr or "Y" in p.freqstr: return p.strftime("%Y")
        return str(p)
    return str(p)

def format_first_listen_table(df_new, name_col, datetime_col="datetime"):
    df_out = df_new.copy()

    if pd.api.types.is_datetime64_any_dtype(df_out[datetime_col]):
        df_out[datetime_col] = df_out[datetime_col].dt.tz_convert(LOCAL_TZ)

    df_out = df_out.sort_values(datetime_col, ascending=True)
    df_out["First Listen"] = df_out[datetime_col].dt.strftime("%d/%m/%Y %H:%M:%S")
    df_out = df_out[[name_col, "First Listen"]]
    df_out.columns = df_out.columns.str.title()

    return df_out

def apply_time_filter(df, filter_name):
    if filter_name == "Morning":
        return df[(df["datetime"].dt.hour >= 6) & (df["datetime"].dt.hour < 12)]
    elif filter_name == "Afternoon":
        return df[(df["datetime"].dt.hour >= 12) & (df["datetime"].dt.hour < 21)]
    elif filter_name == "Night":
        return df[(df["datetime"].dt.hour >= 21) | (df["datetime"].dt.hour < 6)]
    return df

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
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("W")
    elif period == "day":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.date
    elif period == "month":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("M")
    elif period == "year":
        df["Period"] = df["datetime"].dt.tz_convert(LOCAL_TZ).dt.to_period("Y")

    summary = df.groupby("Period").agg(
        Minutes=("duration", lambda x: round(x.sum()/60, 2)),
        Plays=("duration", "count"),
        Median_Year=("year_release", "median")
    ).reset_index()

    summary["Median_Year"] = summary["Median_Year"].round(2)

    artist_minutes = df.groupby(["Period","artist"])["duration"].sum().reset_index()
    idx = artist_minutes.groupby("Period")["duration"].idxmax()
    top_artist = artist_minutes.loc[idx, ["Period","artist"]].rename(columns={"artist":"Top Artist"})
    summary = summary.merge(top_artist, on="Period", how="left")

    track_minutes = df.groupby(["Period","track"])["duration"].sum().reset_index()
    idx = track_minutes.groupby("Period")["duration"].idxmax()
    top_track = track_minutes.loc[idx, ["Period","track"]].rename(columns={"track":"Top Track"})
    summary = summary.merge(top_track, on="Period", how="left")

    album_col = "album_clean" if "album_clean" in df.columns else "album"
    if album_col in df.columns:
        album_minutes = df.groupby(["Period", album_col])["duration"].sum().reset_index()
        idx = album_minutes.groupby("Period")["duration"].idxmax()
        top_album = album_minutes.loc[idx, ["Period", album_col]].rename(columns={album_col: "Top Album"})
        summary = summary.merge(top_album, on="Period", how="left")

    temp = df.dropna(subset=["year_release"]).copy()
    temp["decade"] = temp["year_release"].apply(get_decade)
    decade_minutes = temp.groupby(["Period","decade"])["duration"].sum().reset_index()
    idx = decade_minutes.groupby("Period")["duration"].idxmax()
    top_decade = decade_minutes.loc[idx, ["Period","decade"]].rename(columns={"decade":"Top Decade"})
    summary = summary.merge(top_decade, on="Period", how="left")

    summary = summary.sort_values("Period")
    return summary

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
    df_summary = df_summary.copy()
    minutes_total = df_summary["Minutes"].sum()
    plays_total = df_summary["Plays"].sum()

    df_summary["Minutes%"] = (df_summary["Minutes"] / minutes_total * 100) if minutes_total > 0 else 0.0
    df_summary["Plays%"] = (df_summary["Plays"] / plays_total * 100) if plays_total > 0 else 0.0
    return df_summary

def longest_streak(series):
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

def longest_consecutive_block_details(df, key_col):
    if df.empty or key_col not in df.columns:
        return None, 0, None, None

    s = df.sort_values("datetime").copy()
    s = s[s[key_col].notna()]
    if s.empty:
        return None, 0, None, None

    s["prev_val"] = s[key_col].shift()
    s["new_block"] = s[key_col] != s["prev_val"]
    s["block"] = s["new_block"].cumsum()

    counts = s.groupby([key_col, "block"]).size().rename("size").reset_index()
    best_idx = counts["size"].idxmax()
    best = counts.loc[best_idx]
    val = best[key_col]
    block_id = best["block"]
    size = int(best["size"])

    block_df = s[(s[key_col] == val) & (s["block"] == block_id)].sort_values("datetime")
    first_dt = block_df["datetime"].min()
    last_dt  = block_df["datetime"].max()

    return val, size, first_dt, last_dt

def longest_consecutive_block_minutes(df, key_col):
    if df.empty or key_col not in df.columns or "duration" not in df.columns:
        return None, 0.0, None, None

    s = df.sort_values("datetime").copy()
    s = s[s[key_col].notna()]
    s = s[s["duration"].notna()]
    if s.empty:
        return None, 0.0, None, None

    s["prev_val"] = s[key_col].shift()
    s["new_block"] = s[key_col] != s["prev_val"]
    s["block"] = s["new_block"].cumsum()

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

def get_quick_range(preset: str, tz_name: str = "Europe/Madrid"):
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    today = now.date()

    def at_start_of_day(d):
        return tz.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    def at_end_of_day(d):
        return tz.localize(datetime(d.year, d.month, d.day, 23, 59, 59, 999999))

    if preset in ["Último día", "Last Day"]: return now - timedelta(days=1), now
    if preset in ["Última semana", "Last Week"]: return now - timedelta(days=7), now
    if preset in ["Último mes", "Last Month"]: return now - timedelta(days=30), now
    if preset in ["Últimos 3 meses", "Last 3 Months"]: return now - timedelta(days=90), now
    if preset in ["Últimos 6 meses", "Last 6 Months"]: return now - timedelta(days=180), now
    if preset in ["YTD (año en curso)", "YTD (Year to Date)"]: return tz.localize(datetime(today.year, 1, 1, 0, 0, 0)), now
    if preset in ["Último año", "Last Year"]: return now - timedelta(days=365), now
    if preset in ["Todo", "All"]: return tz.localize(datetime(1970, 1, 1, 0, 0, 0)), now

    if preset in ["Último día natural", "Last Natural Day"]:
        ayer = today - timedelta(days=1)
        return at_start_of_day(ayer), at_end_of_day(ayer)

    if preset in ["Última semana natural", "Last Natural Week"]:
        weekday = today.weekday()
        start_this_week = today - timedelta(days=weekday)
        start_last_week = start_this_week - timedelta(days=7)
        end_last_week = start_this_week - timedelta(days=1)
        return at_start_of_day(start_last_week), at_end_of_day(end_last_week)

    if preset in ["Último mes natural", "Last Natural Month"]:
        year = today.year
        month = today.month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        first_day = datetime(prev_year, prev_month, 1)
        last_day_num = calendar.monthrange(prev_year, prev_month)[1]
        last_day = datetime(prev_year, prev_month, last_day_num)
        return at_start_of_day(first_day), at_end_of_day(last_day)

    return None, None

def add_period_column(df_in: pd.DataFrame, period: str, tz_name: str) -> pd.DataFrame:
    df_out = df_in.copy()
    if df_out.empty:
        df_out["Period"] = pd.NaT
        return df_out

    if period == "week":
        df_out["Period"] = df_out["datetime"].dt.tz_convert(tz_name).dt.to_period("W")
    elif period == "day":
        df_out["Period"] = df_out["datetime"].dt.tz_convert(tz_name).dt.date
    elif period == "month":
        df_out["Period"] = df_out["datetime"].dt.tz_convert(tz_name).dt.to_period("M")
    elif period == "year":
        df_out["Period"] = df_out["datetime"].dt.tz_convert(tz_name).dt.to_period("Y")
    else:
        df_out["Period"] = df_out["datetime"].dt.tz_convert(tz_name).dt.to_period("M")
    return df_out

def calculate_sessions(df, max_gap_minutes=30):
    if df.empty:
        return pd.DataFrame()
    
    df_sorted = df.sort_values("datetime").copy()
    df_sorted["time_diff"] = df_sorted["datetime"].diff()
    df_sorted["new_session"] = (df_sorted["time_diff"] > pd.Timedelta(minutes=max_gap_minutes)) | df_sorted["time_diff"].isna()
    df_sorted["session_id"] = df_sorted["new_session"].cumsum()
    
    session_stats = df_sorted.groupby("session_id").agg(
        start_time=("datetime", "min"),
        end_time=("datetime", "max"),
        track_count=("track", "count"),
        total_duration=("duration", "sum")
    ).reset_index()
    
    session_stats["time_span"] = (session_stats["end_time"] - session_stats["start_time"]).dt.total_seconds() / 60.0
    session_stats["total_duration_mins"] = session_stats["total_duration"] / 60.0
    session_stats["session_minutes"] = session_stats[["time_span", "total_duration_mins"]].max(axis=1)
    
    return session_stats

def apply_top_n_others(df, column, n, use_others=True, others_label="Others", weight_col="duration"):
    """
    Groups items in a column into Top N and "Others" based on a weight column (usually duration).
    """
    if df.empty or column not in df.columns:
        return df
    
    # Calculate totals per item
    totals = df.groupby(column)[weight_col].sum()
    top_items = totals.nlargest(n).index
    
    df_out = df.copy()
    if use_others:
        df_out.loc[~df_out[column].isin(top_items), column] = others_label
    else:
        df_out = df_out[df_out[column].isin(top_items)]
        
    return df_out
