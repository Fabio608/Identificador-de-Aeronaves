import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Flight Tracker Pro", layout="wide")

# --- BASE DE DATOS (Agrega aquí tus aviones) ---
AIRCRAFT_DB = {
    "944": "e80234",
    "VP-FAZ": "e80999",
    "CC-ABC": "e80111"
}

# --- FUNCIONES ---
def buscar_vuelos_opensky(icao24, fecha):
    if "OSN_USER" not in st.secrets or "OSN_PASS" not in st.secrets:
        return "ERROR_SECRETS"
    
    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    url = "https://opensky-network.org/api/states/history"
    auth = (st.secrets["OSN_USER"], st.secrets["OSN_PASS"])
    params = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    try:
        response = requests.get(url, params=params, auth=auth)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    lin.coords = [(c[1], c[0], c[2]) for c in coordenadas]
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

def procesar_vuelos(states):
    df = pd.DataFrame(states, columns=['icao24', 'callsign', 'origin_country', 'time_position', 
                                       'last_contact', 'longitude', 'latitude', 'baro_altitude', 
                                       'on_ground', 'velocity', 'true_track', 'vertical_rate', 
                                       'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'])
    df = df.sort_values(by='time_position')
    # Detectar pausas de 30 min (1800 seg) para separar vuelos
    df['pausa'] = df['time_position'].diff() > 1800
    df['num_vuelo'] = df['pausa'].fillna(False).cumsum()
    
    return [group[['latitude', 'longitude', 'baro_altitude']].values.tolist() 
            for _, group in df.groupby('num_vuelo')]

# --- INTERFAZ PRINCIPAL ---
st.title("✈️ Flight Tracker: Buscador Rápido")
registro = st.text_input("Ingresa Registro (ej: 944)").strip().upper()
fecha = st.date_input("Fecha")

if st.button("Buscar"):
    icao24 = AIRCRAFT_DB.get(registro)
    if not icao24:
        st.error(f"El registro '{registro}' no está en la base de datos. Agrégalo al diccionario AIRCRAFT_DB.")
    else:
        with st.spinner('Procesando datos desde OpenSky...'):
            datos = buscar_vuelos_opensky(icao24, fecha)
            
            if datos == "ERROR_SECRETS":
                st.error("❌ Configura tus credenciales en los Secrets de Streamlit.")
            elif datos and 'states' in datos and datos['states']:
                vuelos = procesar_vuelos(datos['states'])
                st.success(f"✅ Se encontraron {len(vuelos)} tramos de vuelo.")
                
                for i, coords in enumerate(vuelos):
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"✈️ Tramo {i+1}: {len(coords)} puntos de datos registrados.")
                    
                    archivo = generar_kmz(f"Vuelo_{i+1}", coords)
                    col2.download_button(
                        label="Descargar KMZ",
                        data=archivo,
                        file_name=f"vuelo_{registro}_{i+1}.kmz",
                        key=f"dl_{i}"
                    )
                    st.divider()
            else:
                st.warning("No se encontraron registros para esa aeronave en la fecha seleccionada.")
