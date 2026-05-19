import os
import json
import requests
import simplekml
import streamlit as st
from datetime import datetime, timedelta

# =====================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT
# =====================================================================
st.set_page_config(page_title="Identificador de Aeronaves", page_icon="🛩️", layout="centered")

st.title("🛩️ Rastreador Histórico de Aeronaves")
st.markdown("""
Esta aplicación busca la actividad de tus aviones de interés durante el día de ayer 
en la red de **ADSB.fi** y genera archivos KMZ tridimensionales para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"
FICHERO_VIGILANCIA = "vigilancia.json"

# =====================================================================
# FUNCIONES LÓGICAS
# =====================================================================
def obtener_fecha_ayer():
    """Calcula automáticamente la fecha del día anterior en formato YYYY-MM-DD"""
    ayer = datetime.now() - timedelta(days=1)
    return ayer.strftime("%Y-%m-%d")

def cargar_lista_vigilancia():
    """Lee el archivo JSON local con las aeronaves a buscar"""
    try:
        with open(FICHERO_VIGILANCIA, "r") as f:
            return json.load(f).get("aviones_vip", {})
    except FileNotFoundError:
        # Estructura inicial de ejemplo por si el archivo no existe en el repo
        ejemplo = {
            "aviones_vip": {
                "34612a": "Aeronave de Prueba 1",
                "484bb8": "Aeronave de Prueba 2"
            }
        }
        with open(FICHERO_VIGILANCIA, "w") as f:
            json.dump(ejemplo, f, indent=4)
        return ejemplo["aviones_vip"]

def generar_kmz_bytes(hex_code, descripcion, puntos_vuelo, fecha_str):
    """Procesas los puntos y devuelve el archivo KMZ en memoria (bytes) para Streamlit"""
    kml = simplekml.Kml()
    coordenadas = []
    
    for p in puntos_vuelo:
        try:
            lat = p[0]
            lon = p[1]
            alt_pies = p[2]
            
            if alt_pies == "ground" or not alt_pies:
                alt_metros = 0
            else:
                alt_metros = int(alt_pies) * 0.3048
                
            coordenadas.append((lon, lat, alt_metros))
        except (IndexError, ValueError):
            continue

    if not coordenadas:
        return None

    # Configuración de la traza en Google Earth
    ruta = kml.newlinestring(name=f"Vuelo {hex_code} - {descripcion}")
    ruta.coords = coordenadas
    ruta.extrude = 1  # Pared transparente hacia el suelo
    ruta.altitudemode = simplekml.AltitudeMode.absolute
    ruta.style.linestyle.color = simplekml.Color.red  # Línea roja
    ruta.style.linestyle.width = 4
    
    # Marcador de inicio
    marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
    marcador.description = f"Avión: {descripcion}\nCódigo HEX: {hex_code}\nFecha: {fecha_str}"

    # Guardamos temporalmente para pasarlo a bytes
    nombre_temporal = f"temp_{hex_code}.kmz"
    kml.savekmz(nombre_temporal)
    
    # Leemos los bytes del archivo y luego lo borramos para no llenar el servidor de basura
    with open(nombre_temporal, "rb") as f:
        kmz_bytes = f.read()
    os.remove(nombre_temporal)
    
    return kmz_bytes

# =====================================================================
# FLUJO PRINCIPAL DE LA APLICACIÓN (UI)
# =====================================================================
fecha_ayer = obtener_fecha_ayer()
aviones_a_buscar = cargar_lista_vigilancia()

# Mostrar la lista de vigilancia actual en pantalla
st.sidebar.header("📋 Lista de Vigilancia")
if aviones_a_buscar:
    for h_code, desc in aviones_a_buscar.items():
        st.sidebar.markdown(f"- **{h_code.upper()}**: {desc}")
else:
    st.sidebar.warning("La lista de vigilancia está vacía.")

# Botón principal para ejecutar el análisis
if st.button("🛰️ Iniciar Análisis del Día Anterior", type="primary"):
    st.info(f"Buscando actividad del día: **{fecha_ayer}**...")
    
    vuelos_totales_detectados = 0
    progreso = st.progress(0)
    total_aviones = len(aviones_a_buscar)
    
    if total_aviones == 0:
        st.warning("⚠️ No hay aviones configurados en el archivo `vigilancia.json`.")
    else:
        # Iterar sobre los objetivos
        for index, (hex_code, descripcion) in enumerate(aviones_a_buscar.items()):
            hex_code = hex_code.lower().strip()
            dos_primeros = hex_code[:2]
            
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{hex_code}.json"
            
            try:
                respuesta = requests.get(url_peticion, timeout=15)
                
                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])
                    
                    if len(puntos) >= 5:
                        vuelos_totales_detectados += 1
                        st.success(f"🚨 **¡Detectado!** {descripcion} [{hex_code.upper()}] registró {len(puntos)} posiciones.")
                        
                        # Generar el KMZ en memoria
                        kmz_data = generar_kmz_bytes(hex_code, descripcion, puntos, fecha_ayer)
                        
                        if kmz_data:
                            # Botón de descarga nativo de Streamlit para el usuario
                            st.download_button(
                                label=f"📥 Descargar KMZ de {descripcion}",
                                data=kmz_data,
                                file_name=f"traza_{hex_code}_{fecha_ayer}.kmz",
                                mime="application/vnd.google-earth.kmz",
                                key=f"btn_{hex_code}"
                            )
                elif respuesta.status_code != 404:
                    st.warning(f"⚠️ Error al consultar {descripcion} ({hex_code}): Código {respuesta.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error(f"❌ Tiempo de espera agotado para el avión {descripcion}.")
            except Exception as e:
                st.error(f"❌ Error inesperado con {descripcion}: {e}")
            
            # Actualizar barra de progreso
            progreso.progress((index + 1) / total_aviones)
            
        # Mensaje final del análisis
        if vuelos_totales_detectados == 0:
            st.info(f"💤 **Chequeo finalizado:** Ninguno de tus aviones listados registró vuelos ayer ({fecha_ayer}).")
        else:
            st.balloons()
            st.success(f"✨ ¡Proceso terminado! Se detectaron un total de {vuelos_totales_detectados} vuelos.")
