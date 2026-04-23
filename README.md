# Music Stats Dashboard | Tablero de Estadisticas Musicales

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://musicstats.streamlit.app/)

## Overview

Music Stats Dashboard is a professional analytics application designed to provide deep insights into music listening habits. Built with Streamlit and Python, it transforms raw listening history into interactive visualizations, detailed rankings, and behavioral patterns. The platform supports multi-language interfaces and offers a modular architecture for comprehensive music data exploration.

## Descripcion General

Music Stats Dashboard es una aplicacion profesional de analisis diseñada para proporcionar una vision profunda de los habitos de escucha musical. Construida con Streamlit y Python, transforma el historial de reproduccion en visualizaciones interactivas, clasificaciones detalladas y patrones de comportamiento. La plataforma cuenta con soporte multilingüe y ofrece una arquitectura modular para una exploracion exhaustiva de los datos musicales.

---

## Core Features | Caracteristicas Principales

### 1. Global Analytics | Analisis Global
- **Dynamic Filtering**: Comprehensive filters for date ranges (presets and custom), time of day, and release years.
- **Metrics Summary**: Real-time calculation of total listening time, play counts, and unique artist discovery.
- **Filtros Dinamicos**: Filtros exhaustivos por rangos de fechas (predefinidos y personalizados), momentos del dia y años de lanzamiento.
- **Resumen de Metricas**: Calculo en tiempo real del tiempo total de escucha, recuento de reproducciones y descubrimiento de nuevos artistas.

### 2. Rankings and Leaderboards | Clasificaciones y Rankings
- **Granular Rankings**: Top charts for tracks, artists, albums, and genres with percentage share and first-listen dates.
- **Streak Analysis**: Identification of longest listening streaks for specific artists or tracks.
- **Rankings Granulares**: Listas de los mas escuchados para canciones, artistas, albumes y generos, incluyendo porcentaje de cuota y fechas de primera escucha.
- **Analisis de Rachas**: Identificacion de las rachas de escucha mas largas para artistas o canciones especificas.

### 3. Time Patterns and Rhythms | Patrones Temporales y Ritmos
- **Activity Heatmaps**: GitHub-style activity calendars visualizing listening density over the years.
- **Hourly Distribution**: Detailed analysis of listening habits across different hours of the day.
- **Mapas de Calor**: Calendarios de actividad estilo GitHub que visualizan la densidad de escucha a lo largo de los años.
- **Distribucion Horaria**: Analisis detallado de los habitos de escucha segun las diferentes horas del dia.

### 4. Advanced Visualizations (Galaxy) | Visualizaciones Avanzadas (Galaxia)
- **Genre Flow**: Streamgraph visualizations showing the evolution of musical genres over time.
- **Artist Mosaic**: Hierarchical treemaps exploring the relationship between genres, artists, and albums.
- **Music Rings**: Interactive sunburst charts for multi-level exploration of the listening library.
- **Flujo de Generos**: Visualizaciones tipo streamgraph que muestran la evolucion de los generos musicales en el tiempo.
- **Mosaico de Artistas**: Mapas arboreos jerarquicos que exploran la relacion entre generos, artistas y albumes.
- **Anillos Musicales**: Graficos de anillos interactivos para la exploracion multinivel de la biblioteca de escucha.

### 5. Behavioral Analysis (Music DNA) | Analisis de Comportamiento (ADN Musical)
- **Session Tracking**: Automatic detection of listening sessions and marathons.
- **Diversity Index**: Calculation of the Shannon Diversity Index to measure musical taste entropy.
- **Seguimiento de Sesiones**: Deteccion automatica de sesiones y maratones de escucha.
- **Indice de Diversidad**: Calculo del Indice de Diversidad de Shannon para medir la entropia de los gustos musicales.

### 6. Milestones and Achievements | Hitos y Logros
- **Chronological Timeline**: A historical record of significant milestones reached (e.g., reaching X plays for an artist).
- **Milestone Filtering**: Ability to filter achievements by category, artist, or decade.
- **Cronologia Historica**: Un registro historico de los hitos significativos alcanzados (por ejemplo, alcanzar X reproducciones de un artista).
- **Filtrado de Hitos**: Capacidad para filtrar logros por categoria, artista o decada.

---

## Technical Stack | Stack Tecnico

- **Core**: Python 3.10+
- **Web Framework**: Streamlit
- **Data Manipulation**: Pandas, NumPy
- **Visualizations**: Plotly, Scipy
- **Timezone Handling**: Pytz

---

## Installation | Instalacion

1. Clone the repository | Clone el repositorio:
   ```bash
   git clone https://github.com/aleex-cs/music_stats.git
   ```

2. Install dependencies | Instale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application | Ejecute la aplicacion:
   ```bash
   streamlit run app.py
   ```

---

## Data Requirements | Requisitos de Datos

The application expects CSV files located in the `data/` directory with the following structure:
La aplicacion espera archivos CSV ubicados en el directorio `data/` con la siguiente estructura:

- **scrobbles.csv**: Raw listening history (uts, artist, track, album).
- **musica_metadata.csv**: Enhanced metadata (genre, year_release, duration).

---

## Development and Contributions | Desarrollo y Contribuciones

This project is designed with a modular structure, where each tab is handled by a specific module in the `tabs/` directory. Utility functions are centralized in the `utils/` directory to ensure consistency across the application.

Este proyecto esta diseñado con una estructura modular, donde cada pestaña es gestionada por un modulo especifico en el directorio `tabs/`. Las funciones de utilidad estan centralizadas en el directorio `utils/` para garantizar la consistencia en toda la aplicacion.
