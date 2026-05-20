import requests
import time
import datetime
import simplekml
from pathlib import Path

# ================= CONFIGURACIÓN =================
ICAO = "4064d5"          # ICAO hex del avión (ej: ZM415 del A400M)
CALLSIGN = "EMPEROR"     # Opcional
DURACION_MINUTOS = 120   # Cuánto tiempo rastrear
INTERVALO_SEGUNDOS = 5   # Cada cuántos segundos pedir datos

# ================================================

positions = []
start_time = time.time()

print(f"🛫 Iniciando rastreo del avión {CALLSIGN} ({ICAO})...")

while (time.time() - start_time) < DURACION_MINUTOS * 60:
    try:
        response = requests.get(
            f"https://opensky-network.org/api/states/all?icao24={ICAO.lower()}"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['states']:
                state = data['states'][0]
                # [0=icao, 5=lat, 6=lon, 7=baro_altitude, 8=velocity, 9=true_track, 10=vertical_rate]
                lat = state[6]
                lon = state[5]
                alt = state[7]
                speed = state[8]
                heading = state[9]
                
                if lat and lon:
                    positions.append((lat, lon, alt or 0, heading or 0))
                    print(f"📍 {len(positions)} puntos → Lat: {lat}, Lon: {lon}, Alt: {alt}m")
    except:
        pass
    
    time.sleep(INTERVALO_SEGUNDOS)

# ================= GENERAR KMZ =================
kml = simplekml.Kml()

# Línea del recorrido
linestring = kml.newlinestring(name=f"{CALLSIGN} - Track")
linestring.coords = [(lon, lat, alt) for lat, lon, alt, _ in positions]
linestring.altitudemode = simplekml.AltitudeMode.absolute
linestring.extrude = 1
linestring.tessellate = 1
linestring.style.linestyle.color = simplekml.Color.red
linestring.style.linestring.width = 4

# Icono del avión al final
if positions:
    pnt = kml.newpoint(name=CALLSIGN, coords=[(positions[-1][1], positions[-1][0], positions[-1][2])])
    pnt.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/airports.png"

# Guardar
fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M")
archivo = f"{CALLSIGN}_{fecha}.kmz"
kml.save(archivo)
print(f"✅ Archivo guardado: {archivo}")
