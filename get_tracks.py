import io
import os
import csv
from ppadb.client import Client as AdbClient
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

import subprocess
import webbrowser

# Forzamos el inicio usando la ruta que acabas de encontrar
adb_path = r"C:\Users\alexc\Downloads\platform-tools\adb.exe"
subprocess.run([adb_path, "start-server"], capture_output=True)

webbrowser.open("https://mainstream.ghan.nl/export.html")

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("No se encontró ningún dispositivo.")
    exit()

device = devices[0]
print(f"Conectado con éxito a: {device.serial}")

remote_music_folder = "/sdcard/Music"
csv_file = "C:/Users/alexc/Documents/IDK/Música/appStreamlit/data/musica_metadata2.csv"

# -----------------------------
# Leer archivos ya procesados
# -----------------------------
processed_files = set()

if os.path.exists(csv_file):
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            processed_files.add(row[0])

# -----------------------------
# Listar archivos ordenados por fecha (más nuevos primero)
# -----------------------------
files = device.shell(
    f'find "{remote_music_folder}" -type f -printf "%T@ %p\n" | sort -nr'
).splitlines()

files = [line.split(" ", 1)[1] for line in files]

music_files = [f for f in files if f.split(".")[-1].lower() in ["mp3", "flac"]]

# -----------------------------
# Abrir CSV en modo append
# -----------------------------
with open(csv_file, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    total = len(music_files)

    for i, remote_path in enumerate(music_files, 1):

        file_name = remote_path.split("/")[-1]

        # si ya existe → parar
        if file_name in processed_files:
            print(f"[{i}/{total}] Ya procesado, saltando: {file_name}")
            continue

        print(f"[{i}/{total}] Procesando: {file_name}")

        ext = file_name.split(".")[-1].lower()

        try:
            local_tmp = f"./tmp_{file_name}"

            # Descargar el archivo completo
            device.pull(remote_path, local_tmp)

            # -----------------------------
            # Leer metadata
            # -----------------------------
            if ext == "mp3":
                audio_id3 = ID3(local_tmp)
                audio_dur = MP3(local_tmp)

                title = audio_id3.get("TIT2").text[0] if "TIT2" in audio_id3 else ""
                artist = audio_id3.get("TPE1").text[0] if "TPE1" in audio_id3 else ""
                album = audio_id3.get("TALB").text[0] if "TALB" in audio_id3 else ""
                track = audio_id3.get("TRCK").text[0] if "TRCK" in audio_id3 else ""
                genre = audio_id3.get("TCON").text[0] if "TCON" in audio_id3 else ""
                year = audio_id3.get("TDRC").text[0] if "TDRC" in audio_id3 else ""
                duration = round(audio_dur.info.length, 2)

            else:  # flac
                audio = FLAC(local_tmp)

                title = audio.get("title", [""])[0]
                artist = audio.get("artist", [""])[0]
                album = audio.get("album", [""])[0]
                track = audio.get("tracknumber", [""])[0]
                genre = audio.get("genre", [""])[0]
                year = audio.get("date", [""])[0]
                duration = round(audio.info.length, 2)

            # Guardar en CSV
            writer.writerow([file_name, title, artist, album, track, genre, year, duration])

            os.remove(local_tmp)

        except Exception as e:
            print(f"No se pudo procesar {file_name}: {e}")

print("Actualización completada.")