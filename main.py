import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Flight Tracker Pro", layout="wide")

# --- Función para obtener datos reales ---
def buscar_vuelos_opensky(icao24, fecha):
    # Verificación de seguridad de los secretos
    if "OSN_USER" not in st.secrets or "OSN_PASS" not in st.secrets:
        st.error("❌ Error: No has configurado 'OSN_USER' o 'OSN_PASS' en los Secrets de Streamlit.")
        return None
        
    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    url = "https://opensky-network.org/api/states/history"
    auth = (st.secrets["OSN_USER"], st.secrets["OSN_PASS"])
    params = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    try:
        response = requests.get(url, params=params, auth=auth)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"La API respondió con código: {response.status_code}. Revisa tus credenciales.")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- Interfaz ---
st.title("✈️ Flight Tracker Pro")
icao_input = st.text_input("Ingresa ICAO24 (ej: e80234)").strip()
fecha_input = st.date_input("Fecha")

if st.button("Buscar en OpenSky"):
    if icao_input:
        datos = buscar_vuelos_opensky(icao_input, fecha_input)
        if datos:
            st.success("✅ Datos recibidos con éxito.")
            st.json(datos)
    else:
        st.warning("Por favor ingresa un código ICAO24.")
