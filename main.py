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
Configurá tu lista de vigilancia por **Matrícula** a la izquierda y presioná el botón para buscar la actividad 
de ayer en la red de **ADSB.fi**. Genera archivos KMZ tridimensionales para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# =====================================================================
# GESTIÓN DE MEMORIA TEMPORAL (SESSION STATE)
# =====================================================================
# Iniciamos la lista indexada directamente por la Matrícula/Nombre
if "lista_aviones" not in st.session_state:
    st.session_state.lista_aviones = {
        "34612a": "Aeronave Militar Ejemplo 1",
        "ae0133": "C-17 Globemaster USAF",
        "484bb8": "Aeronave VIP Ejemplo 2"
    }

# =====================================================================
# PANEL LATERAL: GESTIÓN ÚNICAMENTE POR MATRÍCULA
# =====================================================================
st.sidebar.header("🛠️ Panel de Vigilancia")

st.sidebar.subheader("➕ Agregar / Editar Objetivo")
# Dejamos un solo casillero de texto para la Matrícula
nueva_matricula = st.sidebar.text_input("Matrícula de la Aeronave (Ej: 933 DHC)").strip()

if st.sidebar.button("💾 Guardar en la Lista"):
    if nueva_matricula:
        # Usamos una versión limpia en minúsculas y sin espacios como "clave" interna,
        # pero guardamos el texto original tal cual lo escribió el usuario para mostrarlo.
        clave_interna = nueva_matricula.lower().replace(" ", "")
        st.session_state.lista_aviones[clave_interna] = nueva_matricula
        st.sidebar.success(f"Matrícula '{nueva_matricula}' guardada.")
        st.rerun()
    else:
        st.sidebar.error("Por favor, ingresá una matrícula válida.")

st.sidebar.markdown("---")

# Listado actual de matrículas con opción de eliminar
st.sidebar.subheader("📋 Matrículas en Vigilancia")
aviones_a_buscar = st.session_state.lista_aviones

if aviones_a_buscar:
    for clave, matricula in list(aviones_a_buscar.items()):
        col_texto, col_borrar = st.sidebar.columns([4, 1])
        col_texto.markdown(f"✈️ **{matricula}**")
        
        # Botón para eliminar la matrícula de la lista
        if col_borrar.button("🗑️", key=f"del_{clave}"):
            del st.session_state.lista_aviones[clave]
            st.rerun()
else:
    st.sidebar.warning("La lista está vacía. Agregá una matrícula arriba.")

# =====================================================================
# CUERPO PRINCIPAL: EJECUCIÓN DEL ANÁLISIS
# =====================================================================
st.subheader("🛰️ Control de Rastreo")

if st.button("🚀 Iniciar Análisis del Día Anterior", type="primary"):
    
    if not aviones_a_buscar:
        st.warning("⚠️ No tenés aeronaves configuradas. Agregá algunas matrículas a la izquierda primero.")
    else:
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        st.info(f"Consultando registros históricos del día: **{fecha_ayer}**...")
        
        vuelos_totales_detectados = 0
        progreso = st.progress(0)
        total_aviones = len(aviones_a_buscar)
        
        # Empezamos el rastreo usando la matrícula como identificador para la API
        for index, (clave, matricula) in enumerate(aviones_a_buscar.items()):
            # La API de ADSB.fi requiere los dos primeros caracteres para la ruta de la carpeta
            dos_primeros = clave[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{clave}.json"
            
            try:
                respuesta = requests.get(url_peticion, timeout=10)
                
                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])
                    
                    if puntos and len(puntos) >= 5:
                        vuelos_totales_detectados += 1
                        st.success(f"🚨 **¡Movimiento Detectado!** Aeronave: {matricula}")
                        
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
                            ruta.extrude = 1  # Paredes verticales proyectadas al terreno
                            ruta.altitudemode = simplekml.AltitudeMode.absolute
                            ruta.style.linestyle.color = simplekml.Color.red
                            ruta.style.linestyle.width = 4
                            
                            marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                            marcador.description = f"Aeronave Matrícula: {matricula}\nFecha: {fecha_ayer}"
                            
                            # Preparación de descarga en memoria
                            nombre_temporal = f"temp_{clave}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)
                            
                            # Botón de descarga directo en la web
                            st.download_button(
                                label=f"📥 Descargar KMZ de {matricula}",
                                data=kmz_data,
                                file_name=f"traza_{clave}_{fecha_ayer}.kmz",
                                mime="application/vnd.google-earth.kmz",
                                key=f"btn_{clave}"
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
