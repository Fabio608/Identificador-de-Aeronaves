import os
import re
import requests
import pandas as pd
import simplekml
import streamlit as st
from bs4 import BeautifulSoup
from datetime import datetime

# ============================================================
# CONFIG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Auditor y Procesador FR24",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Estación de Monitoreo y Procesamiento FR24 ➡️ KMZ")
st.markdown("""
Este panel te permite **auditar la actividad de tus aeronaves de interés** para encontrar los enlaces de Playback exactos en Flightradar24 
y, a la vez, **procesar y limpiar los archivos descargados** con tu licencia para generar mapas 3D perfectos.
""")

# ============================================================
# LISTADO DE FAVORITOS
# ============================================================
AERONAVES_INTERES = {
    "TC-66 (Lockheed C-130H Hércules)": "tc-66",
    "TC-61 (Lockheed C-130H Hércules)": "tc-61",
    "LV-FQZ (Boeing 737 Aerolíneas)": "lv-fqz",
    "ZM421 (Airbus A400M RAF)": "zm421"
}

# Creamos dos pestañas en la interfaz para separar las herramientas
tab1, tab2 = st.tabs(["🔍 Módulo 1: Auditoría y Enlaces", "🛠️ Módulo 2: Procesador de Archivos (Generar KMZ)"])

# ============================================================
# PESTAÑA 1: AUDITORÍA Y ENLACES (SCRAPING)
# ============================================================
with tab1:
    st.subheader("📋 Buscador de Actividad Reciente")
    st.markdown("Averiguá qué días registró movimientos la aeronave y obtené los accesos directos al Playback con su ID integrado.")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        modo_seleccion = st.radio("Objetivo de búsqueda:", ["Mis Favoritos", "Cargar Matrícula Manual"], key="modo_auditor")
        if modo_seleccion == "Mis Favoritos":
            nombre_comun = st.selectbox("Seleccioná la aeronave:", list(AERONAVES_INTERES.keys()))
            matricula_auditar = AERONAVES_INTERES[nombre_comun]
        else:
            matricula_auditar = st.text_input("Ingresá la matrícula (Ej: TC-66):", "").strip().lower().replace(" ", "")
            
        ejecutar_escaneo = st.button("🚀 Escanear Actividad", type="primary")

    def escanear_historial_fr24(matricula_avion):
        url = f"https://www.flightradar24.com/data/aircraft/{matricula_avion}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9"
        }
        vuelos_encontrados = []
        try:
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            filas_tabla = soup.find_all("tr", class_="data-row")
            for fila in filas_tabla:
                celdas = fila.find_all("td")
                if len(celdas) < 9:
                    continue
                fecha_raw = celdas[2].text.strip() if celdas[2] else "Desconocida"
                origen = celdas[3].text.strip() if celdas[3] else "---"
                destino = celdas[4].text.strip() if celdas[4] else "---"
                origen = re.sub(r'\s+', ' ', origen)
                destino = re.sub(r'\s+', ' ', destino)
                callsign = celdas[5].find("a").text.strip() if celdas[5].find("a") else (celdas[5].text.strip() if celdas[5] else "---")
                estado = celdas[8].text.strip() if celdas[8] else "---"
                estado = re.sub(r'\s+', ' ', estado)
                flight_id = fila.get("data-playback", None)
                if origen == "---" and destino == "---":
                    continue
                vuelos_encontrados.append({
                    "Fecha": fecha_raw,
                    "Vuelo/Callsign": callsign,
                    "Origen": origen,
                    "Destino": destino,
                    "Estado del Vuelo": estado,
                    "flight_id": flight_id
                })
        except:
            return None
        return vuelos_encontrados

    with col_der:
        if ejecutar_escaneo:
            if not matricula_auditar:
                st.warning("⚠️ Ingresá una matrícula válida.")
            else:
                with st.spinner("Buscando registros en la red..."):
                    historial = escanear_historial_fr24(matricula_auditar)
                if historial:
                    df = pd.DataFrame(historial)
                    st.success(f"✔️ Se detectaron {len(df)} movimientos recientes para {matricula_auditar.upper()}.")
                    st.dataframe(df[["Fecha", "Vuelo/Callsign", "Origen", "Destino", "Estado del Vuelo"]], use_container_width=True)
                    
                    st.markdown("#### 🔗 Enlaces directos verificados:")
                    for vuelo in historial:
                        if vuelo["flight_id"]:
                            link_playback = f"https://www.flightradar24.com/data/aircraft/{matricula_auditar}#{vuelo['flight_id']}"
                            st.markdown(f"🔹 **{vuelo['Fecha']}** ({vuelo['Origen']} ➡️ {vuelo['Destino']}) — [Abrir Playback Oficial en FR24]({link_playback})")
                else:
                    st.warning("💤 No se encontraron registros públicos recientes o el servidor rechazó la conexión. Intentá ingresando la matrícula manualmente.")

# ============================================================
# PESTAÑA 2: PROCESADOR DE ARCHIVOS (GENERADOR KMZ)
# ============================================================
with tab2:
    st.subheader("🛠️ Limpiador y Convertidor Avanzado de Trazas")
    st.markdown("""
    Arrastrá el archivo histórico que descargaste desde tu cuenta de Flightradar24 (Acepta formatos **.csv** o **.kml** nativos de FR24). 
    El script procesará la geometría, corregirá las altitudes y creará un archivo KMZ profesional tridimensional extrusionado.
    """)
    
    archivo_subido = st.file_uploader("Subí tu archivo de track de FR24 aquí:", type=["csv", "kml"])
    
    # Selector estético para el color de la línea en Google Earth
    color_linea = st.selectbox("Seleccioná el color de la traza para Google Earth:",
