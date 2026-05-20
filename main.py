import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Flight Tracker Pro", layout="wide")

# --- Funciones ---
def buscar_vuelos_opensky(icao24, fecha):
    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    url = "https://opensky-network.org/api/states/history"
    # Autenticación plana (ahora sí funcionará con tus Secrets)
    auth = (st.secrets["OSN_USER"], st.secrets["OSN_PASS"])
    params = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    response = requests.get(url, params=params, auth=auth)
    return response.json() if response.status_code == 200 else None

def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    # coords: [(lon, lat, alt)]
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    lin.coords = [(c[1], c[0], c[2]) for c in coordenadas]
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

# --- Interfaz ---
st.title("✈️ Flight Tracker Pro")
icao_input = st.text_input("Ingresa ICAO24 (ej: e80234)").strip()
fecha_input = st.date_input("Fecha")

if st.button("Buscar en OpenSky"):
    if icao_input:
        datos = buscar_vuelos_opensky(icao_input, fecha_input)
        if datos:
            st.success("Datos recibidos correctamente.")
            # Aquí procesarías el JSON de la API
            st.json(datos) # Mostramos el JSON para que verifiques que llega la info
        else:
            st.error("No se encontraron datos. Verifica tu usuario/pass en los Secrets.")
    else:
        st.warning("Ingresa un código ICAO24.")
