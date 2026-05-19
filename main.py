import streamlit as st
import pandas as pd
import requests
import re
import os
import simplekml
from bs4 import BeautifulSoup
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="Auditor FR24", layout="wide")
st.title("🛰️ Estación de Monitoreo FR24")

# Listado de interés
AERONAVES_INTERES = {
    "TC-66 (Hércules)": "tc-66",
    "TC-61 (Hércules)": "tc-61",
    "LV-FQZ (B737)": "lv-fqz"
}

# Navegación Lateral
st.sidebar.header("Menú")
modulo = st.sidebar.selectbox("Herramienta:", ["Auditoría de Vuelos", "Procesador KMZ"])

# --- MÓDULO 1 ---
if modulo == "Auditoría de Vuelos":
    st.subheader("Buscador de Actividad")
    matricula = st.text_input("Ingresá matrícula (ej: tc-66):")
    if st.button("Buscar"):
        url = f"https://www.flightradar24.com/data/aircraft/{matricula}"
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            filas = soup.find_all("tr", class_="data-row")
            
            for fila in filas:
                celdas = fila.find_all("td")
                if len(celdas) > 5:
                    fecha = celdas[2].text.strip()
                    ruta = f"{celdas[3].text.strip()} ➡️ {celdas[4].text.strip()}"
                    f_id = fila.get("data-playback")
                    st.write(f"📅 **{fecha}** | {ruta}")
                    if f_id:
                        link = f"https://www.flightradar24.com/data/aircraft/{matricula}#{f_id}"
                        st.link_button("Ver Playback", link)
        except Exception as e:
            st.error("Error al conectar con FR24. Verificá la matrícula.")

# --- MÓDULO 2 ---
elif modulo == "Procesador de Archivos (KMZ)":
    st.subheader("Generador de KMZ")
    archivo = st.file_uploader("Subir archivo de traza:", type=["csv", "kml"])
    
    if archivo:
        coords = []
        # Lógica simplificada para leer CSV
        try:
            df = pd.read_csv(archivo)
            # Asumimos columnas lat, lon, alt comunes en FR24
            for _, fila in df.iterrows():
                lat = float(fila['Latitude'])
                lon = float(fila['Longitude'])
                alt = float(fila['Altitude']) * 0.3048 # pies a metros
                coords.append((lon, lat, alt))
            
            kml = simplekml.Kml()
            ruta = kml.newlinestring(coords=coords)
            ruta.altitudemode = simplekml.AltitudeMode.absolute
            ruta.extrude = 1
            
            nombre_salida = "traza_final.kmz"
            kml.savekmz(nombre_salida)
            with open(nombre_salida, "rb") as f:
                st.download_button("Descargar KMZ", f, "resultado.kmz")
            os.remove(nombre_salida)
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")
