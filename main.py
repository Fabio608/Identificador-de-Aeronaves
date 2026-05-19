import os
import requests
import simplekml
import streamlit as st
from datetime import datetime, timedelta

# =====================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT
# =====================================================================
st.set_page_config(page_title="Identificador de Aeronaves", page_icon="🛩️", layout="wide")

st.title("🛩️ Rastreador Histórico de Aeronaves")
st.markdown("""
Configurá tu lista de vigilancia personalizada a la izquierda y presioná el botón para buscar la actividad 
de ayer en la red de **ADSB.fi**. Genera archivos KMZ tridimensionales para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# =====================================================================
# GESTIÓN DE MEMORIA TEMPORAL (SESSION STATE)
# =====================================================================
# Si es la primera vez que abre la app, cargamos unos aviones de ejemplo
if "lista_aviones" not in st.session_state:
    st.session_state.lista_aviones = {
        "34612a": "Aeronave Militar Ejemplo 1",
        "ae0133": "C-17 Globemaster USAF",
        "484bb8": "Aeronave VIP Ejemplo 2"
    }

# =====================================================================
# PANEL LATERAL: AGREGAR, EDITAR Y GESTIONAR AERONAVES
# =====================================================================
st.sidebar.header("🛠️ Panel de Vigilancia")

# Formulario para agregar o editar un avión
st.sidebar.subheader("➕ Agregar / Editar Aeronave")
nuevo_hex = st.sidebar.text_input("Código HEX (Ej: 34612a)", max_chars=6, help="Código hexadecimal único de 6 caracteres").lower().strip()
nueva_desc = st.sidebar.text_input("Nombre o Matrícula (Ej: 933 DHC)")

if st.sidebar.button("💾 Guardar en la Lista"):
    if nuevo_hex and nueva_desc:
        st.session_state.lista_aviones[nuevo_hex] = nueva_desc
        st.sidebar.success(f"Avión [{nuevo_hex.upper()}] guardado con éxito.")
        st.rerun()  # Recarga la interfaz para mostrar los cambios
    else:
        st.sidebar.error("Por favor, completa ambos campos.")

st.sidebar.markdown("---")

# Listado actual con opción de eliminar
st.sidebar.subheader("📋 Objetivos Actuales")
aviones_a_buscar = st.session_state.lista_aviones

if aviones_a_buscar:
    for hex_code, desc in list(aviones_a_buscar.items()):
        col_texto, col_borrar = st.sidebar.columns([4, 1])
        col_texto.markdown(f"**{hex_code.upper()}**: {desc}")
        
        # Botón con un icono de tacho de basura para eliminarlo de la lista
        if col_borrar.button("🗑️", key=f"del_{hex_code}"):
            del st.session_state.lista_aviones[hex_code]
            st.rerun()
else:
    st.sidebar.warning("La lista está vacía. Agrega un avión arriba.")

# =====================================================================
# CUERPO PRINCIPAL: EJECUCIÓN DEL ANÁLISIS
# =====================================================================
st.subheader("🛰️ Control de Rastreo")

# Botón principal de análisis
if st.button("🚀 Iniciar Análisis del Día Anterior", type="primary"):
    
    if not aviones_a_buscar:
        st.warning("⚠️ No tienes aviones configurados en tu lista de vigilancia. Agrega algunos a la izquierda primero.")
    else:
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
                respuesta = requests.get(url_peticion, timeout=10)
                
                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])
                    
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
                            ruta.extrude = 1  
                            ruta.altitudemode = simplekml.AltitudeMode.absolute
                            ruta.style.linestyle.color = simplekml.Color.red
                            ruta.style.linestyle.width = 4
                            
                            marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                            marcador.description = f"Avión: {descripcion}\nHEX: {hex_code}\nFecha: {fecha_ayer}"
                            
                            nombre_temporal = f"temp_{hex_code}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)
                            
                            # Botón para descargar el KMZ generado
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
            
            progreso.progress((index + 1) / total_aviones)
            
        if vuelos_totales_detectados == 0:
            st.info(f"💤 **Sin novedades:** Ninguno de los aviones de tu lista registró movimientos ayer.")
        else:
            st.balloons()
            st.success(f"✨ Análisis finalizado con éxito.")
