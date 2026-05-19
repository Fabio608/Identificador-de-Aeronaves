import streamlit as st
import pandas as pd
import simplekml
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Flight Operations Center", layout="wide")
st.title("🛰️ Flight Operations Center")

# Base de datos local (puedes expandir esto)
if "mis_aeronaves" not in st.session_state:
    st.session_state.mis_aeronaves = ["TC-66", "TC-61", "LV-FQZ"]

# --- 2. GESTOR DE SESIÓN ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.info("Para loguearte: Abre Flightradar24 en tu navegador, inicia sesión y descarga el archivo .CSV de la traza.")
    st.write("---")
    nueva_mat = st.text_input("Registrar nueva aeronave:")
    if st.button("Agregar a la lista"):
        st.session_state.mis_aeronaves.append(nueva_mat.upper())

# --- 3. DASHBOARD DE AERONAVES ---
st.header("✈️ Mis Aeronaves bajo seguimiento")
tabs = st.tabs(st.session_state.mis_aeronaves)

for i, tab in enumerate(tabs):
    with tab:
        mat = st.session_state.mis_aeronaves[i]
        st.subheader(f"Auditoría para: {mat}")
        
        # Área de carga de archivos (Tu puente con FR24)
        archivo = st.file_uploader(f"Cargar traza descargada de FR24 para {mat}:", type=["csv"], key=f"uploader_{mat}")
        
        if archivo:
            if st.button(f"Procesar KMZ de {mat}", key=f"btn_{mat}"):
                df = pd.read_csv(archivo)
                kml = simplekml.Kml()
                coords = []
                
                # Procesamiento automático
                for _, f in df.iterrows():
                    coords.append((float(f['Longitude']), float(f['Latitude']), float(f['Altitude']) * 0.3048))
                
                ruta = kml.newlinestring(name=f"Vuelo {mat}", coords=coords)
                kml.save(f"{mat}_vuelo.kmz")
                
                with open(f"{mat}_vuelo.kmz", "rb") as f:
                    st.download_button(f"📥 Descargar KMZ {mat}", f, f"{mat}_vuelo.kmz")
                os.remove(f"{mat}_vuelo.kmz")
