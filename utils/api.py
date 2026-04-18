import requests
import streamlit as st
import urllib.parse
import json
import os

OVERRIDES_FILE = "data/cover_overrides.json"

def load_overrides():
    if not os.path.exists("data"):
        os.makedirs("data")
    if os.path.exists(OVERRIDES_FILE):
        try:
            with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_override(key: str, url: str):
    overrides = load_overrides()
    overrides[key] = url
    with open(OVERRIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(overrides, f, indent=4)

@st.cache_data(ttl=86400) # Cache for 1 day
def fetch_itunes_results(query: str, limit: int = 5):
    """
    Fetch multiple results from iTunes API for a search query.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://itunes.apple.com/search?term={encoded_query}&entity=album&limit={limit}"
    
    results = []
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("resultCount", 0) > 0:
                for item in data["results"]:
                    artwork_url = item.get("artworkUrl100", "")
                    if artwork_url:
                        high_res = artwork_url.replace("100x100bb", "600x600bb")
                        collection_name = item.get("collectionName", "Unknown Album")
                        artist_name = item.get("artistName", "Unknown Artist")
                        results.append({
                            "url": high_res,
                            "album": collection_name,
                            "artist": artist_name
                        })
    except Exception as e:
        pass
    
    # Optional: fallback to just artist if no results found
    if not results and limit > 1 and " " in query:
        fallback_query = urllib.parse.quote(query.split(" ")[0])
        fallback_url = f"https://itunes.apple.com/search?term={fallback_query}&entity=album&limit={limit}"
        try:
            response = requests.get(fallback_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    artwork_url = item.get("artworkUrl100", "")
                    if artwork_url:
                        high_res = artwork_url.replace("100x100bb", "600x600bb")
                        results.append({
                            "url": high_res,
                            "album": item.get("collectionName", "Unknown"),
                            "artist": item.get("artistName", "Unknown")
                        })
        except:
            pass

    # Deduplicate results based on URL
    unique_results = []
    seen = set()
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
            
    return unique_results

def get_album_cover(artist: str, album: str) -> str:
    """
    Get the album cover, checking overrides first, then calling the cached iTunes search.
    """
    if not artist or not album or str(artist).lower() == "nan" or str(album).lower() == "nan":
        return None
        
    query_key = f"{artist} - {album}".strip().lower()
    
    overrides = load_overrides()
    if query_key in overrides:
        return overrides[query_key]
        
    query = f"{artist} {album}"
    results = fetch_itunes_results(query, limit=1)
    
    if results:
        return results[0]["url"]
        
    return None

@st.cache_data(ttl=86400)
def fetch_deezer_artist(artist: str, limit: int = 5):
    encoded_query = urllib.parse.quote(artist)
    url = f"https://api.deezer.com/search/artist?q={encoded_query}&limit={limit}"
    
    results = []
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("data", []):
                picture = item.get("picture_xl") or item.get("picture_big")
                if picture:
                    results.append({
                        "url": picture,
                        "album": "Artist Image",
                        "artist": item.get("name", "Unknown")
                    })
    except Exception as e:
        pass
    
    unique_results = []
    seen = set()
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
            
    return unique_results

def get_artist_image(artist: str) -> str:
    if not artist or str(artist).lower() == "nan":
        return None
        
    query_key = f"artist_image - {artist}".strip().lower()
    
    overrides = load_overrides()
    if query_key in overrides:
        return overrides[query_key]
        
    results = fetch_deezer_artist(artist, limit=1)
    if results:
        return results[0]["url"]
        
    return None
