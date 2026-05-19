import streamlit as st
import pandas as pd
import requests
import os
import simplekml
from bs4 import BeautifulSoup

# Configuración de la página
st.set_page_config(page_title="Flight Route KMZ Generator", layout="wide")

st.title("🛰️ Flight Route KMZ Generator")
st.markdown("---")

# Menú lateral (Navegación del flujo)
menu = st.sidebar.selectbox("Seleccionar Paso:", ["1. Auditoría (FR24)", "2. Procesamiento de Datos", "3. Exportar KMZ"])

# --- PASO 1: AUDITORÍA (INPUT DE ENLACE) ---
if menu == "1. Auditoría (FR24)":
    st.header("1. Auditoría y Extracción")
    matricula = st.text_input("Matrícula de la Aeronave (ej: tc-66):")
    if st.button("Obtener enlaces de Playback"):
        if matricula:
            url = f"https://www.flightradar24.com/data/aircraft/{matricula.lower()}"
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                filas = soup.find_all("tr", class_="data-row")
                for fila in filas:
                    celdas = fila.find_all("td")
                    if len(celdas) > 5:
                        f_id = fila.get("data-playback")
                        if f_id:
                            link = f"https://www.flightradar24.com/data/aircraft/{matricula.lower()}#{f_id}"
                            st.info(f"Fecha: {celdas[2].text.strip()} | Ruta: {celdas[3].text.strip()} ➡️ {celdas[4].text.strip()}")
                            st.link_button("Abrir Playback", link)
            except:
                st.error("Error al conectar con FR24.")

# --- PASO 2 Y 3: PROCESAMIENTO Y EXPORTACIÓN ---
elif menu == "2. Procesamiento de Datos":
    st.header("2. Procesamiento de Archivo CSV")
    archivo = st.file_uploader("Subí el CSV de la traza:", type=["csv"])
    if archivo:
        df = pd.read_csv(archivo)
        st.write("Vista previa de datos:", df.head())
        st.success("¡Datos cargados correctamente! Ahora ve al paso 3 para exportar.")
        st.session_state['data'] = df

elif menu == "3. Exportar KMZ":
    st.header("3. Generar KMZ")
    if 'data' in st.session_state:
        df = st.session_state['data']
        if st.button("Convertir a KMZ"):
            try:
                coords = []
                # Ajustá los nombres de columnas según tu CSV
                for _, fila in df.iterrows():
                    coords.append((fila['Longitude'], fila['Latitude'], float(fila['Altitude']) * 0.3048))
                
                kml = simplekml.Kml()
                line = kml.newlinestring(name="Ruta de Vuelo", coords=coords)
                line.altitudemode = simplekml.AltitudeMode.absolute
                line.extrude = 1
                
                kml.save("ruta_final.kmz")
                with open("ruta_final.kmz", "rb") as f:
                    st.download_button("Descargar KMZ", f, "ruta.kmz")
            except Exception as e:
                st.error(f"Error procesando: {e}")
    else:
        st.warning("Primero debes procesar el archivo en el paso 2.")
