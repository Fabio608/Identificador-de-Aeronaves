import streamlit as st
import requests
import simplekml
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Extractor GIS de Vuelos", layout="wide", page_icon="✈️")

# --- FUNCIONES AUXILIARES ---
def consultar_api_radares(matricula, fecha_str):
    """Hace la petición a la API y maneja errores de conexión."""
    url = f"https://api.airplanes.live/v2/historical/{matricula}/{fecha_str}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            return None, f"❌ No se encontraron datos para la matrícula {matricula} en la fecha {fecha_str}."
        else:
            return None, f"❌ Error de servidor (Código {response.status_code})."
    except requests.exceptions.Timeout:
        return None, "❌ La conexión con el servidor de radares tardó demasiado."
    except Exception as e:
        return None, f"❌ Ocurrió un error inesperado de red: {e}"

def generar_kmz_aeronautico(matricula, fecha_str, puntos_radar):
    """Procesa los puntos y construye el archivo KMZ estructurado para QGIS."""
    coordenadas_validas = []
    tiempos = []
    
    for p in puntos_radar:
        # Estructura: p[0]= timestamp, p[1]= lat, p[2]= lon, p[3]= altitud
        timestamp = p[0]
        lat = p[1]
        lon = p[2]
        alt = p[3] if p[3] is not None and p[3] != "ground" else 0
        
        if lat is not None and lon is not None:
            coordenadas_validas.append((lat, lon, alt))
            hora_legible = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            tiempos.append(hora_legible)
            
    if not coordenadas_validas:
        return None, None, None

    kml = simplekml.Kml()
    
    # 1. Crear línea continua de la trayectoria
    linea = kml.newlinestring(name=f"Ruta_{matricula}_{fecha_str}")
    linea.coords = [(c[1], c[0], c[2]) for c in coordenadas_validas]
    linea.style.linestyle.color = "ff00ff00"  # Verde brillante en formato KML
    linea.style.linestyle.width = 4
    linea.altitudemode = simplekml.AltitudeMode.absolute
