import streamlit as st

STRINGS = {
    "en": {
        "app_title": "Music Stats",
        "sidebar_filters": "Global Filters",
        "quick_range": "Quick range",
        "start_date": "Start Date",
        "end_date": "End Date",
        "time_period": "Time period",
        "time_of_day": "Time of day",
        "num_rows": "Number of rows",
        "release_year": "Release year range",
        "evolution_top_n": "Series in evolution charts (Top N)",
        "evolution_help": "Number of series (lines) to show in the evolution charts for artists, tracks, albums, and genres.",
        "viz_limits": "Visualization Limits",
        "group_others": "Group into 'Others'",
        "others_help": "If enabled, items outside Top N will be grouped into 'Others'.",
        "decades": "Decades",
        "genres": "Genres",
        "artists": "Artists",
        "albums": "Albums",
        "tracks": "Tracks",
        "applying_range": "Applying range",
        "to": "to",
        "tabs": {
            "home": "🏠 Home",
            "summary": "📈 Summary",
            "rankings": "🏆 Rankings",
            "rhythms": "📅 Time Rhythms",
            "dna": "🧠 Music DNA",
            "explorer": "🔍 Explorer",
            "flashback": "🎁 Flashback",
            "milestones": "👑 Milestones",
            "galaxy": "🪐 Galaxy"
        },
        "home": {
            "title": "Welcome to Your Music World 🎧",
            "subtitle": "Explore your history, discover patterns, and celebrate your milestones",
            "total_time": "Total Time",
            "tracks_heard": "Tracks Heard",
            "unique_artists": "Unique Artists",
            "top_artist": "Top Artist",
            "recent_activity": "Recent Activity",
            "vibe_check": "Vibe Check",
            "vibe_subtitle": "Your dominant genre in this period",
            "daily_dist": "Daily Distribution",
            "most_active_day": "Most Active Day",
            "fire_day": "You were on fire that day!",
            "made_with": "Made with ❤️ for music lovers"
        },
        "data_viewer": {
            "subtitle": "Your most popular tracks, artists, and albums"
        },
        "time_patterns": {
            "subtitle": "When are you most musically active?"
        },
        "behavior": {
            "subtitle": "Deep analysis of your sessions and evolution"
        },
        "searcher": {
            "subtitle": "Filter and find any corner of your history"
        },
        "wrapped": {
            "subtitle": "A visual summary of your recent history"
        },
        "visuals": {
            "subtitle": "Deep visual explorations of your sound universe",
            "others_decade": "Other Decades",
            "others_genre": "Other Genres",
            "others_artist": "Other Artists",
            "others_album": "Other Albums",
            "others_track": "Other Tracks",
            "config_rings": "Configure the rings",
            "ring": "Ring",
            "none": "(none)"
        },
        "milestones": {
            "title": "Milestones Wall 👑",
            "subtitle": "A chronological journey through your biggest achievements",
            "filter_type": "Filter milestones by:",
            "global": "Global",
            "artist": "Artist",
            "track": "Track",
            "decade": "Decade",
            "select_artist": "Select an artist",
            "select_track": "Select a track",
            "select_decade": "Select a decade",
            "timeline": "🏆 Timeline",
            "no_data": "Not enough listening history yet to hit major milestones!"
        }
    },
    "es": {
        "app_title": "Music Stats",
        "sidebar_filters": "Filtros Globales",
        "quick_range": "Rango rápido",
        "start_date": "Fecha de inicio",
        "end_date": "Fecha de fin",
        "time_period": "Periodo de tiempo",
        "time_of_day": "Momento del día",
        "num_rows": "Número de filas",
        "release_year": "Rango de año de lanzamiento",
        "evolution_top_n": "Series en gráficos de evolución (Top N)",
        "evolution_help": "Número de series (líneas) a mostrar en los gráficos de evolución para artistas, pistas, álbumes y géneros.",
        "viz_limits": "Límites de Visualización",
        "group_others": "Agrupar en 'Otros'",
        "others_help": "Si se activa, los elementos fuera del Top N se agruparán en 'Otros'.",
        "decades": "Décadas",
        "genres": "Géneros",
        "artists": "Artistas",
        "albums": "Álbumes",
        "tracks": "Canciones",
        "applying_range": "Aplicando rango",
        "to": "a",
        "tabs": {
            "home": "🏠 Inicio",
            "summary": "📈 Resumen",
            "rankings": "🏆 Rankings",
            "rhythms": "📅 Ritmos",
            "dna": "🧠 ADN Musical",
            "explorer": "🔍 Explorador",
            "flashback": "🎁 Flashback",
            "milestones": "👑 Hitos",
            "galaxy": "🪐 Galaxia"
        },
        "home": {
            "title": "Bienvenido a tu Mundo Musical 🎧",
            "subtitle": "Explora tu historial, descubre patrones y celebra tus hitos",
            "total_time": "Tiempo Total",
            "tracks_heard": "Canciones Escuchadas",
            "unique_artists": "Artistas Distintos",
            "top_artist": "Artista Top",
            "recent_activity": "Actividad Reciente",
            "vibe_check": "Vibe Check",
            "vibe_subtitle": "Tu género dominante en este periodo",
            "daily_dist": "Distribución Diaria",
            "most_active_day": "Día más Activo",
            "fire_day": "¡Ese día estuviste a tope!",
            "made_with": "Hecho con ❤️ para amantes de la música"
        },
        "data_viewer": {
            "subtitle": "Tus canciones, artistas y álbumes más populares"
        },
        "time_patterns": {
            "subtitle": "¿Cuándo eres más activo musicalmente?"
        },
        "behavior": {
            "subtitle": "Análisis profundo de tus sesiones y evolución"
        },
        "searcher": {
            "subtitle": "Filtra y encuentra cualquier rincón de tu historial"
        },
        "wrapped": {
            "subtitle": "Un resumen visual de tu historia reciente"
        },
        "visuals": {
            "subtitle": "Exploraciones visuales profundas de tu universo sonoro",
            "others_decade": "Otras Décadas",
            "others_genre": "Otros Géneros",
            "others_artist": "Otros Artistas",
            "others_album": "Otros Álbumes",
            "others_track": "Otras Canciones",
            "config_rings": "Configura los anillos",
            "ring": "Anillo",
            "none": "(ninguno)"
        },
        "milestones": {
            "title": "Muro de Hitos 👑",
            "subtitle": "Un recorrido cronológico por tus mayores logros",
            "filter_type": "Filtrar hitos por:",
            "global": "Global",
            "artist": "Artista",
            "track": "Canción",
            "decade": "Década",
            "select_artist": "Selecciona un artista",
            "select_track": "Selecciona una canción",
            "select_decade": "Selecciona una década",
            "timeline": "🏆 Cronología",
            "no_data": "¡Aún no hay suficiente historial para mostrar hitos importantes!"
        }
    }
}

def get_text(key, lang="en"):
    parts = key.split(".")
    d = STRINGS.get(lang, STRINGS["en"])
    for p in parts:
        if isinstance(d, dict):
            d = d.get(p, {})
        else:
            d = {}
    if not d or d == {}:
        # Fallback to English
        d = STRINGS["en"]
        for p in parts:
            if isinstance(d, dict):
                d = d.get(p, {})
            else:
                d = {}
    return d if isinstance(d, str) else key
