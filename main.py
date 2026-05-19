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
Configurá tu lista de vigilancia a la izquierda asociando la **Matrícula** con su **Código HEX**. 
El sistema buscará los movimientos del día anterior en la red de **ADSB.fi** y generará archivos KMZ para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# =====================================================================
# GESTIÓN DE MEMORIA TEMPORAL (SESSION STATE)
# =====================================================================
# Iniciamos con el ejemplo real de la RAF que mencionaste y otros
if "lista_aviones" not in st.session_state:
    st.session_state.lista_aviones = {
        "43c5ef": "ZM421 (RAF A400M)",
        "ae0133": "C-17 Globemaster USAF",
        "34612a": "Aeronave Militar Ejemplo"
    }

# =====================================================================
# PANEL LATERAL: GESTIÓN DE OBJETIVOS (MATRÍCULA + HEX)
# =====================================================================
st.sidebar.header("🛠️ Panel de Vigilancia")

st.sidebar.subheader("➕ Agregar / Editar Objetivo")
# Pedimos ambos datos para que la API no falle jamás
nueva_matricula = st.sidebar.text_input("Matrícula o Nombre (Ej: ZM421 RAF)").strip()
nuevo_hex = st.sidebar.text_input("Código HEX de 6 caracteres (Ej: 43C5EF)", max_chars=6).lower().strip()

if st.sidebar.button("💾 Guardar en la Lista"):
    if nueva_matricula and nuevo_hex and len(nuevo_hex) == 6:
        # Guardamos usando el HEX como clave única para la API
        st.session_state.lista_aviones[nuevo_hex] = nueva_matricula
        st.sidebar.success(f"Registrado: {nueva_matricula} [{nuevo_hex.upper()}]")
        st.rerun()
    else:
        st.sidebar.error("Por favor, completá la Matrícula y el código HEX (debe tener 6 caracteres).")

st.sidebar.markdown("---")

# Listado actual de vigilancia
st.sidebar.subheader("📋 Objetivos en Vigilancia")
aviones_a_buscar = st.session_state.lista_aviones

if aviones_a_buscar:
    for hex_code, matricula in list(aviones_a_buscar.items()):
        col_texto, col_borrar = st.sidebar.columns([4, 1])
        col_texto.markdown(f"✈️ **{matricula}** <br><small>HEX: {hex_code.upper()}</small>", unsafe_allow_html=True)
        
        if col_borrar.button("🗑️", key=f"del_{hex_code}"):
            del st.session_state.lista_aviones[hex_code]
            st.rerun()
else:
    st.sidebar.warning("La lista está vacía. Agregá un objetivo arriba.")

# =====================================================================
# CUERPO PRINCIPAL: EJECUCIÓN DEL ANÁLISIS
# =====================================================================
st.subheader("🛰️ Control de Rastreo")

if st.button("🚀 Iniciar Análisis del Día Anterior", type="primary"):
    
    if not aviones_a_buscar:
        st.warning("⚠️ No tenés aeronaves configuradas en tu lista.")
    else:
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        st.info(f"Consultando registros históricos en ADSB.fi del día: **{fecha_ayer}**...")
        
        vuelos_totales_detectados = 0
        progreso = st.progress(0)
        total_aviones = len(aviones_a_buscar)
        
        # El rastreo usa el código HEX real para la consulta web
        for index, (hex_code, matricula) in enumerate(aviones_a_buscar.items()):
            dos_primeros = hex_code[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{hex_code}.json"
            
            try:
                respuesta = requests.get(url_peticion, timeout=10)
                
                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])
                    
                    if puntos and len(puntos) >= 5:
                        vuelos_totales_detectados += 1
                        st.success(f"🚨 **¡Movimiento Detectado!** Aeronave: {matricula} [{hex_code.upper()}]")
                        
                        # Generamos el archivo geográfico KMZ tridimensional
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
                            ruta = kml.newlinestring(name=f"Vuelo - {matricula}")
                            ruta.coords = coordenadas
                            ruta.extrude = 1
                            ruta.altitudemode = simplekml.AltitudeMode.absolute
                            ruta.style.linestyle.color = simplekml.Color.red
                            ruta.style.linestyle.width = 4
                            
                            marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                            marcador.description = f"Aeronave: {matricula}\nHEX: {hex_code.upper()}\nFecha: {fecha_ayer}"
                            
                            nombre_temporal = f"temp_{hex_code}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)
                            
                            st.download_button(
                                label=f"📥 Descargar KMZ de {matricula}",
                                data=kmz_data,
                                file_name=f"traza_{matricula.replace(' ', '_')}_{fecha_ayer}.kmz",
                                mime="application/vnd.google-earth.kmz",
                                key=f"btn_{hex_code}"
                            )
                            
                elif respuesta.status_code != 404:
                    st.warning(f"⚠️ El servidor respondió con código {respuesta.status_code} para {matricula}")
                    
            except requests.exceptions.Timeout:
                st.error(f"⏱️ Tiempo de espera agotado al consultar la aeronave {matricula}.")
            except Exception as e:
                st.error(f"❌ Error inesperado con {matricula}: {e}")
            
            progreso.progress((index + 1) / total_aviones)
            
        if vuelos_totales_detectados == 0:
            st.info(f"💤 **Sin novedades:** Ninguna de las aeronaves de tu lista registró movimientos ayer.")
        else:
            st.balloons()
            st.success(f"✨ Análisis finalizado.")
