import streamlit as st
import pandas as pd
import simplekml
import os

# Configuración de página
st.set_page_config(page_title="Flight Tracker Pro", layout="centered")

# --- BLOQUE 1: Centro de Gestión ---
with st.container(border=True):
    col1, col2 = st.columns([0.1, 0.9])
    with col1: st.write("⚙️")
    with col2:
        st.subheader("Centro de Gestión de Vuelos")
        st.write("Gestiona tus archivos descargados de Flightradar24.")
        st.info("Nota: Para procesar vuelos reales, descarga el archivo CSV desde tu sesión de FR24 y súbelo aquí.")

# --- BLOQUE 2: Mis Aeronaves ---
with st.container(border=True):
    col1, col2 = st.columns([0.1, 0.9])
    with col1: st.write("✈️")
    with col2:
        st.subheader("Mis Aeronaves")
        # Lista de aeronaves que el usuario quiere tener controladas
        if "aeronaves" not in st.session_state:
            st.session_state.aeronaves = ["TC-66", "TC-61", "LV-FQZ"]
        st.write(f"Seguimiento activo: {', '.join(st.session_state.aeronaves)}")

# --- BLOQUE 3: Procesador de Datos ---
with st.container(border=True):
    st.subheader("✈️ Flight Tracker & KMZ")
    
    # Selector de aeronave basada en tu lista
    reg = st.selectbox("Seleccionar Aeronave", st.session_state.aeronaves)
    date = st.date_input("Fecha del vuelo")
    
    # Carga del archivo que tú obtienes de tu cuenta de FR24
    archivo = st.file_uploader("Subir CSV de traza:", type=["csv"])
    
    search_btn = st.button("🚀 Generar KMZ", use_container_width=True, type="primary")

# Lógica de procesamiento (Sin intentos de conexión fallidos)
if search_btn:
    if archivo:
        try:
            df = pd.read_csv(archivo)
            kml = simplekml.Kml()
            coords = []
            
            for _, fila in df.iterrows():
                # Conversión estándar de los archivos de FR24
                coords.append((float(fila['Longitude']), float(fila['Latitude']), float(fila['Altitude']) * 0.3048))
            
            ruta = kml.newlinestring(name=f"Vuelo {reg}", coords=coords)
            ruta.altitudemode = simplekml.AltitudeMode.absolute
            ruta.extrude = 1
            
            nombre_archivo = f"{reg}_{date}.kmz"
            kml.save(nombre_archivo)
            
            with open(nombre_archivo, "rb") as f:
                st.download_button("📥 DESCARGAR KMZ", f, nombre_archivo)
            os.remove(nombre_archivo)
            st.success("¡Archivo generado correctamente!")
            
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}. Asegúrate de que el CSV tenga las columnas Longitude, Latitude y Altitude.")
    else:
        st.warning("Por favor, sube el archivo CSV descargado de Flightradar24.")
