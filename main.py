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
    "944": "e80234",      # Asegúrate de verificar el ICAO24 hex correcto para esta unidad
    "VP-FAZ": "e80999",
    "CC-ABC": "e80111"
}

# --- FUNCIONES ---
def buscar_trayectorias_opensky(icao24, fecha):
    if "OSN_USER" not in st.secrets or "OSN_PASS" not in st.secrets:
        return "ERROR_SECRETS"
    
    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    auth = (st.secrets["OSN_USER"], st.secrets["OSN_PASS"])
    
    # 1. Buscamos los vuelos/tramos registrados en ese día
    url_flights = "https://opensky-network.org/api/flights/aircraft"
    params_flights = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    try:
        res_flights = requests.get(url_flights, params=params_flights, auth=auth)
        if res_flights.status_code != 200:
            return None
        
        vuelos = res_flights.json()
        tramos_procesados = []
        
        # 2. Para cada vuelo, solicitamos su "track" detallado
        for f in vuelos:
            url_track = "https://opensky-network.org/api/tracks/all"
            params_track = {'icao24': icao24, 'time': f['firstSeen']}
            res_track = requests.get(url_track, params=params_track, auth=auth)
            
            if res_track.status_code == 200:
                track_data = res_track.json()
                
                # OpenSky devuelve el path como una lista de listas:
                # [time, latitude, longitude, baro_altitude, true_track, on_ground]
                coords = []
                for p in track_data.get('path', []):
                    lat, lon, alt = p[1], p[2], p[3]
                    # Validamos que existan datos de posición y rellenamos altitud si es Null
                    if lat is not None and lon is not None:
                        alt = alt if alt is not None else 0
                        coords.append((lat, lon, alt))
                
                if coords:
                    tramos_procesados.append({
                        "origen": f.get("estDepartureAirport") or "Desconocido",
                        "destino": f.get("estArrivalAirport") or "Desconocido",
                        "coordenadas": coords
                    })
        return tramos_procesados
    except:
        return None

def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    # simplekml requiere estrictamente: (Longitud, Latitud, Altitud)
    lin.coords = [(c[1], c[0], c[2]) for c in coordenadas]
    
    # Configuración de estilo básica para QGIS
    lin.style.linestyle.color = simplekml.Color.red
    lin.style.linestyle.width = 3
    
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

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
            vuelos = buscar_trayectorias_opensky(icao24, fecha)
            
            if vuelos == "ERROR_SECRETS":
                st.error("❌ Configura tus credenciales en los Secrets de Streamlit.")
            elif vuelos:
                st.success(f"✅ Se encontraron {len(vuelos)} tramos de vuelo.")
                
                for i, vuelo in enumerate(vuelos):
                    col1, col2 = st.columns([3, 1])
                    orig = vuelo["origen"]
                    dest = vuelo["destino"]
                    puntos = len(vuelo["coordenadas"])
                    
                    col1.write(f"✈️ **Tramo {i+1}:** {orig} ➔ {dest} ({puntos} puntos de telemetría).")
                    
                    archivo = generar_kmz(f"Vuelo_{registro}_Tramo_{i+1}", vuelo["coordenadas"])
                    col2.download_button(
                        label="Descargar KMZ",
                        data=archivo,
                        file_name=f"vuelo_{registro}_tramo_{i+1}.kmz",
                        key=f"dl_{i}"
                    )
                    st.divider()
            else:
                st.warning("No se encontraron registros de tracking para esa aeronave en la fecha seleccionada.")
