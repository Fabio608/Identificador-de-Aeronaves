import os
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

# =====================================================================
# CONFIGURACIÓN DE TUS AVIONES (CÓDIGO HEX: DESCRIPCIÓN)
# =====================================================================
def obtener_lista_aviones():
    """
    Acá podés editar tus aviones agregando o sacando líneas.
    Siempre respetando el formato "codigo_hex": "Nombre/Descripción",
    """
    return {
        "34612a": "Aeronave Militar Ejemplo 1",
        "ae0133": "C-17 Globemaster USAF",
        "484bb8": "Aeronave VIP Ejemplo 2"
    }

# =====================================================================
# INTERFAZ DE USUARIO (SIDEBAR Y BOTÓN)
# =====================================================================
aviones_a_buscar = obtener_lista_aviones()

# Mostrar la lista de objetivos a la izquierda
st.sidebar.header("📋 Objetivos en Vigilancia")
for h_code, desc in aviones_a_buscar.items():
    st.sidebar.markdown(f"- **{h_code.upper()}**: {desc}")

# Botón principal
if st.button("🛰️ Iniciar Análisis del Día Anterior", type="primary"):
    
    # Calculamos la fecha de ayer recién cuando el usuario aprieta el botón
    fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    st.info(f"Consultando registros históricos del día: **{fecha_ayer}**...")
    
    vuelos_totales_detectados = 0
    progreso = st.progress(0)
    total_aviones = len(aviones_a_buscar)
    
    # Empezamos el rastreo individual
    for index, (hex_code, descripcion) in enumerate(aviones_a_buscar.items()):
        hex_code = hex_code.lower().strip()
        dos_primeros = hex_code[:2]
        url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{hex_code}.json"
        
        try:
            # Petición rápida con tiempo límite estricto para que no se congele
            respuesta = requests.get(url_peticion, timeout=10)
            
            if respuesta.status_code == 200:
                puntos = respuesta.json().get("trace", [])
                
                # Exigimos al menos 5 posiciones geográficas válidas
                if puntos and len(puntos) >= 5:
                    vuelos_totales_detectados += 1
                    st.success(f"🚨 **¡Movimiento Detectado!** {descripcion} [{hex_code.upper()}]")
                    
                    # Generamos el mapa KML/KMZ tridimensional
                    kml = simplekml.Kml()
                    coordenadas = []
                    
                    for p in puntos:
                        try:
                            lat, lon, alt_pies = p[0], p[1], p[2]
                            alt_metros = 0 if alt_pies == "ground" or not alt_pies else int(alt_pies) * 0.3048
                            coordenadas.append((lon, lat, alt_metros))
                        except:
                            continue
                    
                    if coordenadas:
                        ruta = kml.newlinestring(name=f"Vuelo {hex_code} - {descripcion}")
                        ruta.coords = coordenadas
                        ruta.extrude = 1  # Efecto cortina tridimensional hacia el suelo
                        ruta.altitudemode = simplekml.AltitudeMode.absolute
                        ruta.style.linestyle.color = simplekml.Color.red
                        ruta.style.linestyle.width = 4
                        
                        marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                        marcador.description = f"Avión: {descripcion}\nHEX: {hex_code}\nFecha: {fecha_ayer}"
                        
                        # Conversión segura a bytes para descarga web
                        nombre_temporal = f"temp_{hex_code}.kmz"
                        kml.savekmz(nombre_temporal)
                        with open(nombre_temporal, "rb") as f:
                            kmz_data = f.read()
                        os.remove(nombre_temporal)
                        
                        # Ofrecemos el botón de descarga en la interfaz web
                        st.download_button(
                            label=f"📥 Descargar KMZ de {descripcion}",
                            data=kmz_data,
                            file_name=f"traza_{hex_code}_{fecha_ayer}.kmz",
                            mime="application/vnd.google-earth.kmz",
                            key=f"btn_{hex_code}"
                        )
                        
            elif respuesta.status_code != 404:
                st.warning(f"⚠️ El servidor respondió con error {respuesta.status_code} para {descripcion}")
                
        except requests.exceptions.Timeout:
            st.error(f"⏱️ Tiempo de espera agotado al consultar el avión {descripcion}.")
        except Exception as e:
            st.error(f"❌ Error inesperado con {descripcion}: {e}")
        
        # Avanzar barra de progreso visual
        progreso.progress((index + 1) / total_aviones)
        
    # Mensaje final del proceso
    if vuelos_totales_detectados == 0:
        st.info(f"💤 **Sin novedades:** Ninguno de los aviones listados registró vuelos el día de ayer.")
    else:
        st.balloons()
        st.success(f"✨ Análisis finalizado con éxito.")
