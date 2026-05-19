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
Configurá tu lista de vigilancia únicamente por **Matrícula** a la izquierda. 
El sistema buscará los movimientos del día anterior en la red de **ADSB.fi** y generará archivos KMZ para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# =====================================================================
# GESTIÓN DE MEMORIA TEMPORAL (SESSION STATE)
# =====================================================================
# Iniciamos la lista con ejemplos reales directamente usando su identificador
if "lista_aviones" not in st.session_state:
    st.session_state.lista_aviones = {
        "43c5ef": "43C5EF (RAF ZM421)",
        "ae0133": "AE0133 (C-17 USAF)"
    }

# =====================================================================
# PANEL LATERAL: UN SOLO MENÚ Y UN SOLO CASILLERO
# =====================================================================
st.sidebar.header("🛠️ Panel de Vigilancia")

st.sidebar.subheader("➕ Agregar Objetivo")
# Único casillero de la interfaz lateral
nueva_matricula = st.sidebar.text_input("Matrícula de la Aeronave").strip()

if st.sidebar.button("💾 Guardar en la Lista"):
    if nueva_matricula:
        # Limpiamos espacios y pasamos a minúsculas para que funcione como clave de búsqueda
        clave_busqueda = nueva_matricula.lower().replace(" ", "")
        st.session_state.lista_aviones[clave_busqueda] = nueva_matricula
        st.sidebar.success(f"✈️ {nueva_matricula} agregada.")
        st.rerun()
    else:
        st.sidebar.error("Por favor, ingresá una matrícula.")

st.sidebar.markdown("---")

# Listado limpio con botón para borrar
st.sidebar.subheader("📋 Matrículas en Vigilancia")
aviones_a_buscar = st.session_state.lista_aviones

if aviones_a_buscar:
    for clave, matricula in list(aviones_a_buscar.items()):
        col_texto, col_borrar = st.sidebar.columns([4, 1])
        col_texto.markdown(f"✈️ **{matricula}**")
        
        # Botón directo para eliminar de la lista
        if col_borrar.button("🗑️", key=f"del_{clave}"):
            del st.session_state.lista_aviones[clave]
            st.rerun()
else:
    st.sidebar.warning("La lista está vacía.")

# =====================================================================
# CUERPO PRINCIPAL: EJECUCIÓN DEL ANÁLISIS
# =====================================================================
st.subheader("🛰️ Control de Rastreo")

if st.button("🚀 Iniciar Análisis del Día Anterior", type="primary"):
    
    if not aviones_a_buscar:
        st.warning("⚠️ No tenés aeronaves configuradas en tu lista de vigilancia.")
    else:
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        st.info(f"Consultando registros históricos del día: **{fecha_ayer}**...")
        
        vuelos_totales_detectados = 0
        progreso = st.progress(0)
        total_aviones = len(aviones_a_buscar)
        
        # El bucle recorre la lista limpia usando la clave ingresada
        for index, (clave, matricula) in enumerate(aviones_a_buscar.items()):
            dos_primeros = clave[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{clave}.json"
            
            try:
                respuesta = requests.get(url_peticion, timeout=10)
                
                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])
                    
                    if puntos and len(puntos) >= 5:
                        vuelos_totales_detectados += 1
                        st.success(f"🚨 **¡Movimiento Detectado!** Aeronave: {matricula}")
                        
                        # Generamos el archivo geográfico KMZ tridimensional para Google Earth
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
                            marcador.description = f"Aeronave: {matricula}\nFecha: {fecha_ayer}"
                            
                            nombre_temporal = f"temp_{clave}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)
                            
                            # Ofrecemos la descarga web directa del archivo mapeado
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
            st.success(f"✨ Análisis finalizado con éxito.")
