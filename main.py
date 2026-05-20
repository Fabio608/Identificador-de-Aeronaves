import requests
import simplekml
from datetime import datetime

def obtener_track_adsbfi(registration, fecha_str):
    """
    Obtiene el recorrido y tiempos exactos sin bloqueos.
    fecha_str debe tener formato 'YYYY-MM-DD' (ej: '2026-05-19')
    """
    # ADSB.fi permite buscar directamente por matrícula (registration) el historial de un día
    url = f"https://api.adsb.fi/v2/historical/{registration}/{fecha_str}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
            
        data = response.json()
        points = data.get("trace", []) # Consigue todos los pings de radar del día
        
        coords = []
        for p in points:
            # p[0]= timestamp, p[1]= lat, p[2]= lon, p[3]= altitud
            time_epoch = p[0]
            lat = p[1]
            lon = p[2]
            alt = p[3] if p[3] is not None else 0
            
            # Convertimos el tiempo a formato legible por si querés mostrarlo
            hora_legible = datetime.fromtimestamp(time_epoch).strftime('%H:%M:%S')
            
            coords.append((lat, lon, alt, hora_legible))
            
        return coords
    except:
        return None
