import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Flight Tracker Pro", layout="wide")

# --- Función para obtener datos reales de OpenSky ---
def buscar_vuelos_opensky(icao24, fecha):
    # Convertir fecha a timestamp UNIX
    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    url = "https://opensky-network.org/api/states/history"
    auth = (st.secrets["OPENSKY"]["user"], st.secrets["OPENSKY"]["password"])
    params = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    response = requests.get(url, params=params, auth=auth)
    return response.json() if response.status_code == 200 else None

# --- Función para generar KMZ ---
def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    # coords esperadas: (lon, lat, alt)
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    lin.coords = [(c[1], c[0], c[2]) for c in coordenadas]
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

# --- Interfaz ---
st.title("✈️ Flight Tracker: Motor de Búsqueda Histórica")
icao_input = st.text_input("Ingresa el ICAO24 (ej: e80234)").strip()
fecha_input = st.date_input("Fecha a consultar")

if st.button("Buscar en OpenSky"):
    if icao_input:
        with st.spinner('Consultando servidores de OpenSky...'):
            datos = buscar_vuelos_opensky(icao_input, fecha_input)
            
            if datos and 'states' in datos and datos['states']:
                st.success("¡Datos recuperados con éxito!")
                
                # Procesar datos (la API devuelve una lista de estados)
                # Nota: Esto es una simplificación; la API devuelve estados masivos
                # Aquí crearíamos la lógica para agrupar por trayectorias
                
                # Simulamos visualización de mapa con los datos recibidos
                df = pd.DataFrame(columns=['lat', 'lon']) # Lógica de filtrado aquí
                st.write("Visualización del trayecto detectado:")
                st.map(df)
                
                # Botón de descarga
                archivo = generar_kmz(icao_input, []) # Pasar coordenadas filtradas
                st.download_button("Descargar KMZ", archivo, f"vuelo_{icao_input}.kmz", "application/vnd.google-earth.kmz")
            else:
                st.warning("No se encontraron registros para esta aeronave en esa fecha.")
    else:
        st.error("Por favor ingresa un ICAO24 válido.")
