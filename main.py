import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Flight Tracker Pro", layout="wide")

# --- Función para obtener datos de OpenSky ---
def buscar_vuelos_opensky(icao24, fecha):
    # Verificación de que existen los secretos
    if "OSN_USER" not in st.secrets or "OSN_PASS" not in st.secrets:
        return "ERROR_SECRETS"

    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    url = "https://opensky-network.org/api/states/history"
    auth = (st.secrets["OSN_USER"], st.secrets["OSN_PASS"])
    params = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    try:
        response = requests.get(url, params=params, auth=auth)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# --- Función para generar KMZ ---
def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    # coords esperadas: [(lat, lon, alt)]
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
    if not icao_input:
        st.warning("Por favor ingresa un ICAO24.")
    else:
        with st.spinner('Consultando OpenSky...'):
            resultado = buscar_vuelos_opensky(icao_input, fecha_input)
            
            if resultado == "ERROR_SECRETS":
                st.error("Configuración incorrecta: No se encuentran los datos de acceso en los Secrets.")
            elif resultado:
                st.success("¡Datos recuperados!")
                st.write("JSON recibido:", resultado) # Aquí verás los datos reales
            else:
                st.error("No se encontraron registros o error en la consulta.")
