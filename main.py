import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Flight Tracker Pro", layout="wide")

# --- Funciones ---
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
    # coords esperadas: (lat, lon, alt)
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    lin.coords = [(c[1], c[0], c[2]) for c in coordenadas]
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

def procesar_vuelos(states):
    if not states: return []
    df = pd.DataFrame(states, columns=['icao24', 'callsign', 'origin_country', 'time_position', 
                                       'last_contact', 'longitude', 'latitude', 'baro_altitude', 
                                       'on_ground', 'velocity', 'true_track', 'vertical_rate', 
                                       'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'])
    df = df.sort_values(by='time_position')
    # Detectar pausas de 30 min (1800 seg)
    df['pausa'] = df['time_position'].diff() > 1800
    df['num_vuelo'] = df['pausa'].fillna(False).cumsum()
    
    vuelos = []
    for _, group in df.groupby('num_vuelo'):
        vuelos.append(group[['latitude', 'longitude', 'baro_altitude']].values.tolist())
    return vuelos

# --- Interfaz Principal ---
st.title("✈️ Flight Tracker Pro")
icao_input = st.text_input("Ingresa ICAO24 (ej: e80234)").strip()
fecha_input = st.date_input("Fecha")

if st.button("Buscar en OpenSky"):
    if not icao_input:
        st.warning("Por favor ingresa un ICAO24.")
    else:
        with st.spinner('Procesando datos...'):
            # AQUÍ ES DONDE EL CÓDIGO ANTERIOR FALLABA
            # Nos aseguramos de obtener el resultado primero
            datos_raw = buscar_vuelos_opensky(icao_input, fecha_input)
            
            if datos_raw == "ERROR_SECRETS":
                st.error("❌ Configuración incorrecta: Revisa los Secrets.")
            elif datos_raw and 'states' in datos_raw and datos_raw['states']:
                lista_vuelos = procesar_vuelos(datos_raw['states'])
                st.success(f"✅ Se detectaron {len(lista_vuelos)} vuelos distintos.")
                
                for idx, coords in enumerate(lista_vuelos):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"✈️ Vuelo {idx + 1}: {len(coords)} puntos registrados.")
                    with col2:
                        archivo = generar_kmz(f"Vuelo_{idx+1}", coords)
                        st.download_button("Descargar KMZ", archivo, f"vuelo_{idx+1}.kmz", key=f"dl_{idx}")
                    st.divider()
            else:
                st.warning("No se encontraron registros para esa aeronave en esa fecha.")
