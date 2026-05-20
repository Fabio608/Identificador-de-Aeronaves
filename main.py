import streamlit as st
import requests
import simplekml
import pandas as pd
from io import BytesIO
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Flight Tracker Pro", layout="wide", page_icon="✈️")

# --- BASE DE DATOS DE AERONAVES ---
# Asegúrate de colocar los códigos ICAO de 24 bits (hexadecimal) correctos.
AIRCRAFT_DB = {
    "944": "e80234",      # Ejemplo de ICAO Hex para la unidad buscada
    "VP-FAZ": "e80999",
    "CC-ABC": "e80111"
}

# --- FUNCIONES DE TELEMETRÍA ---
def buscar_trayectorias_opensky(icao24, fecha):
    """
    Consulta la API de OpenSky. Primero busca los tramos de vuelo del día
    y luego descarga la telemetría detallada de cada tramo detectado.
    """
    if "OSN_USER" not in st.secrets or "OSN_PASS" not in st.secrets:
        return "ERROR_SECRETS"
    
    # Convertimos la fecha elegida a Timestamps de Unix (inicio y fin del día)
    ts_inicio = int(datetime.combine(fecha, datetime.min.time()).timestamp())
    ts_fin = int(datetime.combine(fecha, datetime.max.time()).timestamp())
    
    auth = (st.secrets["OSN_USER"], st.secrets["OSN_PASS"])
    
    # Paso 1: Obtener la lista de vuelos/tramos que hizo el avión ese día
    url_flights = "https://opensky-network.org/api/flights/aircraft"
    params_flights = {'icao24': icao24, 'begin': ts_inicio, 'end': ts_fin}
    
    try:
        res_flights = requests.get(url_flights, params=params_flights, auth=auth)
        if res_flights.status_code != 200:
            return None
        
        vuelos = res_flights.json()
        if not vuelos:
            return []
            
        tramos_procesados = []
        
        # Paso 2: Para cada tramo de vuelo, pedir el "track" de puntos detallado
        for f in vuelos:
            url_track = "https://opensky-network.org/api/tracks/all"
            params_track = {'icao24': icao24, 'time': f['firstSeen']}
            res_track = requests.get(url_track, params=params_track, auth=auth)
            
            if res_track.status_code == 200:
                track_data = res_track.json()
                coords = []
                
                # El "path" de OpenSky es una lista de listas con este formato:
                # [time, latitude, longitude, baro_altitude, true_track, on_ground]
                for p in track_data.get('path', []):
                    lat, lon, alt = p[1], p[2], p[3]
                    if lat is not None and lon is not None:
                        alt = alt if alt is not None else 0  # Reemplaza nulos por altitud 0
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
    """
    Genera un archivo KMZ compatible con QGIS y Google Earth Pro 
    manteniendo las propiedades 3D de la trayectoria.
    """
    kml = simplekml.Kml()
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    
    # IMPORTANTE: simplekml requiere estrictamente el orden (Longitud, Latitud, Altitud)
    lin.coords = [(c[1], c[0], c[2]) for c in coordenadas]
    
    # Configuración estética básica para identificarlo fácil en QGIS
    lin.style.linestyle.color = "ff0000ff"  # Rojo en formato hexadecimal KML (AABBGGRR)
    lin.style.linestyle.width = 3
    
    # Habilitamos que interprete la altitud respecto al nivel del mar
    lin.altitudemode = simplekml.AltitudeMode.absolute
    
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("✈️ Flight Tracker Pro: Extractor GIS de Trayectorias")
st.markdown("Busca el historial de vuelos diarios de una aeronave y descarga los vectores estructurados en formato KMZ para mapear en QGIS.")

# Panel de inputs usando columnas para mejorar el diseño
col_input1, col_input2 = st.columns(2)
with col_input1:
    registro = st.text_input("Ingresa el Registro / Matrícula interna (ej: 944)").strip().upper()
with col_input2:
    fecha = st.date_input("Selecciona la Fecha de Análisis", value=datetime.today())

st.markdown("---")

if st.button("🔍 Buscar Historial de Vuelo", type="primary"):
    if not registro:
        st.warning("Por favor, ingresa una matrícula para iniciar la búsqueda.")
    else:
        # Obtenemos el código ICAO hexadecimal asociado a la matrícula en nuestro diccionario
        icao24 = AIRCRAFT_DB.get(registro)
        
        if not icao24:
            st.error(f"❌ La matrícula '{registro}' no está registrada en el diccionario `AIRCRAFT_DB` en el código. Agrégala al inicio del script para poder buscarla.")
        else:
            with st.spinner('Conectando con OpenSky Network y descargando coordenadas aeronáuticas...'):
                vuelos = buscar_trayectorias_opensky(icao24, fecha)
                
                if vuelos == "ERROR_SECRETS":
                    st.error("❌ Error de configuración: Faltan las credenciales `OSN_USER` y `OSN_PASS` en los Secrets de tu cuenta de Streamlit.")
                
                elif vuelos is None:
                    st.error("❌ No se pudo establecer conexión con los servidores de OpenSky. Revisa tus credenciales o el estado de la API.")
                
                elif len(vuelos) == 0:
                    st.warning(f"⚠️ No se encontraron registros de telemetría o tracks de radar para la aeronave (ICAO24: {icao24}) en la fecha seleccionada ({fecha}).")
                
                else:
                    st.success(f"✅ ¡Éxito! Se encontraron {len(vuelos)} tramos de vuelo independientes para el día seleccionado.")
                    
                    # Desplegamos los tramos encontrados para descarga masiva individual
                    for i, vuelo in enumerate(vuelos):
                        orig = vuelo["origen"]
                        dest = vuelo["destino"]
                        puntos = len(vuelo["coordenadas"])
                        
                        # Caja visual para cada tramo de la ruta
                        with st.container():
                            col_info, col_dl = st.columns([3, 1])
                            
                            with col_info:
                                st.markdown(f"### ✈️ Tramo {i+1}")
                                st.write(f"**Ruta estimada:** `{orig}` ➔ `{dest}`")
                                st.write(f"**Puntos de posición registrados (Pings de radar):** {puntos}")
                            
                            with col_dl:
                                # Generamos el archivo binario KMZ en memoria
                                archivo_kmz = generar_kmz(f"Vuelo_{registro}_Tramo_{i+1}", vuelo["coordenadas"])
                                
                                st.download_button(
                                    label="💾 Descargar KMZ",
                                    data=archivo_kmz,
                                    file_name=f"vuelo_{registro}_tramo_{i+1}_{fecha}.kmz",
                                    mime="application/vnd.google-earth.kmz",
                                    key=f"btn_dl_{i}"
                                )
                            st.markdown("---")
