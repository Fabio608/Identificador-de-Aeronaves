import streamlit as st
import pandas as pd
import requests
import os
import simplekml
from bs4 import BeautifulSoup
from io import BytesIO

# Configuración básica
st.set_page_config(page_title="Auditor FR24", layout="wide")
st.title("🛰️ Estación de Monitoreo FR24")

# Menú lateral para evitar errores de pestañas
modulo = st.sidebar.selectbox("Seleccionar herramienta:", ["Auditoría de Vuelos", "Procesador KMZ"])

# --- MÓDULO 1: AUDITORÍA ---
if modulo == "Auditoría de Vuelos":
    st.subheader("Buscador de actividad de aeronaves")
    matricula = st.text_input("Ingresá la matrícula (ej: tc-66):")

    if st.button("Buscar en FR24"):
        if not matricula:
            st.warning("Por favor, ingresá una matrícula.")
        else:
            url = f"https://www.flightradar24.com/data/aircraft/{matricula.lower()}"
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                filas = soup.find_all("tr", class_="data-row")

                if not filas:
                    st.error("No se encontraron datos o el servidor bloqueó la consulta.")
                else:
                    for fila in filas:
                        celdas = fila.find_all("td")
                        if len(celdas) > 5:
                            fecha = celdas[2].text.strip()
                            ruta_text = f"{celdas[3].text.strip()} ➡️ {celdas[4].text.strip()}"
                            f_id = fila.get("data-playback")

                            st.write(f"📅 **{fecha}** | {ruta_text}")
                            if f_id:
                                link = f"https://www.flightradar24.com/data/aircraft/{matricula.lower()}#{f_id}"
                                st.markdown(f"[Ir al Playback]({link})", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error técnico: {e}")

# --- MÓDULO 2: PROCESADOR ---
elif modulo == "Procesador KMZ":
    st.subheader("Convertidor a KMZ profesional")
    archivo = st.file_uploader("Subir archivo CSV de traza:", type=["csv"])

    if archivo:
        try:
            df = pd.read_csv(archivo)

            # Detectar columnas latitud, longitud y altitud
            lat_cols = [c for c in df.columns if 'lat' in c.lower()]
            lon_cols = [c for c in df.columns if 'lon' in c.lower()]
            alt_cols = [c for c in df.columns if 'alt' in c.lower()]

            if not lat_cols or not lon_cols or not alt_cols:
                st.error("No se encontraron columnas con latitud, longitud o altitud en el archivo.")
            else:
                lat_col = lat_cols[0]
                lon_col = lon_cols[0]
                alt_col = alt_cols[0]

                coords = []
                for _, fila in df.iterrows():
                    lat = float(fila[lat_col])
                    lon = float(fila[lon_col])
                    alt = float(fila[alt_col]) * 0.3048  # Conversión pies a metros
                    coords.append((lon, lat, alt))

                kml = simplekml.Kml()
                ruta = kml.newlinestring(name="Traza", coords=coords)
                ruta.altitudemode = simplekml.AltitudeMode.absolute
                ruta.extrude = 1

                # Guardar KML en buffer para evitar archivos temporales
                kmz

