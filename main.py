import streamlit as st
import pandas as pd
import requests
import simplekml
import os
from bs4 import BeautifulSoup
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="Flight Auditor Pro", layout="wide")
st.title("🛰️ Flight Route KMZ Generator")

# Inicializar estado para la Flota
if "mis_aeronaves" not in st.session_state:
    st.session_state.mis_aeronaves = ["TC-66", "TC-61", "LV-FQZ"]

# --- SIDEBAR: GESTIÓN ---
st.sidebar.header("Gestión de Flota")
nueva_mat = st.sidebar.text_input("Nueva matrícula:")
if st.sidebar.button("Agregar"):
    if nueva_mat and nueva_mat not in st.session_state.mis_aeronaves:
        st.session_state.mis_aeronaves.append(nueva_mat.upper())

# --- BLOQUE 1: AUDITORÍA ---
with st.container(border=True):
    st.subheader("🔍 1. Auditoría de Vuelo")
    col1, col2 = st.columns(2)
    with col1:
        reg = st.selectbox("Aeronave:", st.session_state.mis_aeronaves)
    with col2:
        fecha_busqueda = st.date_input("Fecha a buscar:")

    if st.button("Verificar actividad"):
        url = f"https://www.flightradar24.com/data/aircraft/{reg.lower()}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            encontrado = False
            for fila in soup.find_all("tr", class_="data-row"):
                fecha_str = fila.find_all("td")[2].text.strip()
                if fecha_busqueda.strftime("%d/%m/%y") in fecha_str:
                    st.success(f"✅ Vuelo encontrado el {fecha_str}")
                    encontrado = True
                    break
            if not encontrado:
                st.warning("No se detectaron vuelos para esa fecha.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

# --- BLOQUE 2: PROCESAMIENTO ---
with st.container(border=True):
    st.subheader("🛠️ 2. Generar KMZ")
    archivo = st.file_uploader("Subir CSV de traza (descargado de FR24):", type=["csv"])
    
    if archivo:
        if st.button("Convertir a .KMZ"):
            try:
                df = pd.read_csv(archivo)
                # Búsqueda automática de columnas
                lat_c = next((c for c in df.columns if 'lat' in c.lower()), None)
                lon_c = next((c for c in df.columns if 'lon' in c.lower()), None)
                alt_c = next((c for c in df.columns if 'alt' in c.lower()), None)
                
                kml = simplekml.Kml()
                coords = [(float(f[lon_c]), float(f[lat_c]), float(f[alt_c])*0.3048) for _, f in df.iterrows()]
                
                ruta = kml.newlinestring(name=f"Vuelo {reg}", coords=coords)
                ruta.altitudemode = simplekml.AltitudeMode.absolute
                ruta.extrude = 1
                
                nombre = f"{reg}_vuelo.kmz"
                kml.save(nombre)
                with open(nombre, "rb") as f:
                    st.download_button("📥 DESCARGAR KMZ", f, nombre)
                os.remove(nombre)
                st.balloons()
            except Exception as e:
                st.error(f"Error procesando el archivo: {e}")
