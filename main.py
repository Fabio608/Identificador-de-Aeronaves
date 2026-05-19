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

# ============================================================
# LISTADO DE FAVORITOS
# ============================================================
AERONAVES_INTERES = {
    "TC-66 (Lockheed C-130H Hércules)": "tc-66",
    "TC-61 (Lockheed C-130H Hércules)": "tc-61",
    "LV-FQZ (Boeing 737 Aerolíneas)": "lv-fqz",
    "ZM421 (Airbus A400M RAF)": "zm421"
}

# ============================================================
# NAV BAR LATERAL (Reemplaza a las pestañas bugueadas)
# ============================================================
st.sidebar.header("🗺️ Menú de Navegación")
modulo_activo = st.sidebar.selectbox(
    "Seleccioná la herramienta:",
    ["🔍 Módulo 1: Auditoría y Enlaces", "🛠️ Módulo 2: Procesador de Archivos (KMZ)"]
)

# ============================================================
# MÓDULO 1: AUDITORÍA Y ENLACES
# ============================================================
if modulo_activo == "🔍 Módulo 1: Auditoría y Enlaces":
    st.subheader("📋 Buscador de Actividad Reciente")
    st.markdown("Averiguá qué días registró movimientos la aeronave y obtené los accesos directos al Playback con su ID integrado.")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        modo_seleccion = st.radio("Objetivo de búsqueda:", ["Mis Favoritos", "Cargar Matrícula Manual"])
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
                    st.warning("⚠️ No se pudieron recuperar los registros. FR24 puede estar saturado. Intentá de nuevo en unos instantes.")

# ============================================================
# MÓDULO 2: PROCESADOR DE ARCHIVOS (GENERADOR KMZ)
# ============================================================
elif modulo_activo == "🛠️ Módulo 2: Procesador de Archivos (KMZ)":
    st.subheader("🛠️ Limpiador y Convertidor Avanzado de Trazas")
    st.markdown("""
    Arrastrá el archivo histórico que descargaste desde tu cuenta de Flightradar24 (Soporta formatos **.csv** o **.kml** nativos). 
    El script procesará la geometría, corregirá las altitudes y creará un archivo KMZ profesional tridimensional extrusionado.
    """)
    
    archivo_subido = st.file_uploader("Subí tu archivo de track de FR24 aquí:", type=["csv", "kml"])
    
    color_linea = st.selectbox("Seleccioná el color de la traza para Google Earth:", ["Rojo Intenso", "Verde Militar", "Azul Aeronáutico", "Amarillo Alerta"])
    color_map = {
        "Rojo Intenso": simplekml.Color.red,
        "Verde Militar": simplekml.Color.green,
        "Azul Aeronáutico": simplekml.Color.blue,
        "Amarillo Alerta": simplekml.Color.yellow
    }

    if archivo_subido is not None:
        st.info("📦 Archivo recibido. Iniciando ingeniería de datos geométrica...")
        coords_procesadas = []
        nombre_archivo = archivo_subido.name
        
        try:
            # CASO A: Archivo CSV
            if nombre_archivo.endswith(".csv"):
                df_csv = pd.read_csv(archivo_subido)
                col_lat = [c for c in df_csv.columns if 'lat' in c.lower() or 'position' in c.lower()][0]
                col_lon = [c for c in df_csv.columns if 'lon' in c.lower() or 'position' in c.lower()][0]
                col_alt = [c for c in df_csv.columns if 'alt' in c.lower()][0]
                
                for idx, fila in df_csv.iterrows():
                    try:
                        if col_lat == col_lon:
                            lat_val, lon_val = map(float, str(fila[col_lat]).split(','))
                        else:
                            lat_val = float(fila[col_lat])
                            lon_val = float(fila[col_lon])
                        
                        alt_pies = fila[col_alt]
                        alt_m = 0 if str(alt_pies).lower() in ["ground", "none", "nan"] else float(alt_pies) * 0.3048
                        coords_procesadas.append((lon_val, lat_val, alt_m))
                    except:
                        continue
                        
            # CASO B: Archivo KML nativo
            elif nombre_archivo.endswith(".kml"):
                contenido_kml = archivo_subido.read().decode("utf-8")
                bloques_coords = re.findall(r"<coordinates>(.*?)</coordinates>", contenido_kml, re.DOTALL)
                
                for bloque in bloques_coords:
                    puntos = bloque.strip().split()
                    for p in puntos:
                        try:
                            partes = p.split(",")
                            if len(partes) >= 2:
                                lon_val = float(partes[0])
                                lat_val = float(partes[1])
                                alt_original = float(partes[2]) if len(partes) >= 3 else 0
                                alt_m = alt_original if alt_original > 10000 else alt_original * 0.3048
                                coords_procesadas.append((lon_val, lat_val, alt_m))
                        except:
                            continue

            if len(coords_procesadas) < 2:
                st.error("❌ El archivo no contiene suficientes puntos geométricos válidos.")
            else:
                st.success(f"📊 ¡Éxito! Se procesaron {len(coords_procesadas)} puntos de tracking tridimensional.")
                
                with st.spinner("Modelando el espacio aéreo 3D y estructurando el archivo KMZ..."):
                    kml = simplekml.Kml()
                    ruta_3d = kml.newlinestring(name=f"Track Procesado - {nombre_archivo}")
                    ruta_3d.coords = coords_procesadas
                    ruta_3d.style.linestyle.color = color_map[color_linea]
                    ruta_3d.style.linestyle.width = 4
                    ruta_3d.altitudemode = simplekml.AltitudeMode.absolute
                    ruta_3d.extrude = 1 
                    
                    kml.newpoint(name="Punto de Partida", coords=[coords_procesadas[0]])
                    kml.newpoint(name="Última Posición", coords=[coords_procesadas[-1]])
                    
                    archivo_salida = "traza_procesada.kmz"
                    kml.savekmz(archivo_salida)
                    
                    with open(archivo_salida, "rb") as f:
                        kmz_bytes = f.read()
                    os.remove(archivo_salida)
                
                st.success("🎉 ¡Tu archivo KMZ optimizado para Google Earth Pro está listo!")
                st.download_button(
                    label="📥 DESCARGAR KMZ PROCESADO",
                    data=kmz_bytes,
                    file_name=f"procesado_{nombre_archivo.split('.')[0]}.kmz",
                    mime="application/vnd.google-earth.kmz",
                    type="primary"
                )
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Error al parsear la estructura del archivo: {e}")
