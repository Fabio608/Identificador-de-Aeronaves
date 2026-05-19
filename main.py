import streamlit as st
import pandas as pd
import requests
import simplekml
import os
from bs4 import BeautifulSoup

st.set_page_config(page_title="Flight Auditor & KMZ Pro", layout="wide")
st.title("🛰️ Auditor y Generador KMZ")

# --- 1. GESTIÓN DE FLOTA ---
if "mis_aeronaves" not in st.session_state:
    st.session_state.mis_aeronaves = ["TC-66", "TC-61", "LV-FQZ"]

# --- 2. INTERFAZ DE BÚSQUEDA ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        reg = st.selectbox("Seleccionar aeronave:", st.session_state.mis_aeronaves)
    with col2:
        fecha_busqueda = st.date_input("Fecha a buscar:")

    if st.button("🔍 Verificar si voló y obtener datos"):
        # Lógica de scraping para verificar el día
        url = f"https://www.flightradar24.com/data/aircraft/{reg.lower()}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Buscamos en el historial del avión
        encontrado = False
        for fila in soup.find_all("tr", class_="data-row"):
            fecha_str = fila.find_all("td")[2].text.strip()
            # Si la fecha coincide con la del input
            if fecha_busqueda.strftime("%d/%m/%y") in fecha_str:
                flight_id = fila.get("data-playback")
                st.success(f"✅ ¡Vuelo detectado el {fecha_str}!")
                st.session_state['flight_id'] = flight_id
                encontrado = True
                break
        
        if not encontrado:
            st.warning("No se detectaron vuelos para esa fecha.")

# --- 3. PROCESAMIENTO A KMZ ---
if 'flight_id' in st.session_state:
    st.info("Ahora subí el archivo de traza que descargaste de FR24 para esa fecha:")
    archivo = st.file_uploader("Subir CSV de FR24", type=["csv"])
    
    if archivo:
        if st.button("Convertir a .KMZ"):
            df = pd.read_csv(archivo)
            kml = simplekml.Kml()
            coords = []
            
            # Asumimos columnas estándar
            for _, fila in df.iterrows():
                coords.append((fila['Longitude'], fila['Latitude'], float(fila['Altitude']) * 0.3048))
            
            ruta = kml.newlinestring(name=f"Vuelo {reg}", coords=coords)
            ruta.altitudemode = simplekml.AltitudeMode.absolute
            ruta.extrude = 1
            
            nombre_kmz = f"{reg}_{fecha_busqueda}.kmz"
            kml.save(nombre_kmz)
            
            with open(nombre_kmz, "rb") as f:
                st.download_button("📥 DESCARGAR KMZ FINAL", f, nombre_kmz)
            os.remove(nombre_kmz)
