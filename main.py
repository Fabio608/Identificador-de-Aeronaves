import streamlit as st
import requests
import simplekml
from io import BytesIO
import time

st.set_page_config(page_title="Flight Tracker", layout="centered")

st.title("✈️ Flight Tracker Engine")
st.markdown("---")

# --- Lógica de Generación de KMZ ---
def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    # Simplekml espera (longitud, latitud, altitud)
    coords = [(p[1], p[0], p[2]) for p in coordenadas]
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    lin.coords = coords
    lin.style.linestyle.width = 5
    lin.style.linestyle.color = 'ff0000ff' # Rojo
    
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

# --- Interfaz Principal ---
icao_input = st.text_input("ICAO24 (Código hex, ej: e80234)")
fecha = st.date_input("Fecha del vuelo")

if st.button("Buscar Traza Histórica"):
    if icao_input:
        st.info(f"Buscando vuelos para {icao_input}...")
        # AQUÍ ES DONDE LUEGO CONECTAREMOS TU CUENTA DE OPENSKY
        # Simulación de datos recibidos:
        mis_coordenadas = [
            (-45.8, -67.5, 5000), 
            (-45.9, -67.6, 5100), 
            (-46.0, -67.7, 5200)
        ]
        
        st.success("¡Datos encontrados!")
        
        # Botón de descarga
        archivo = generar_kmz(icao_input, mis_coordenadas)
        st.download_button(
            label="Descargar KMZ",
            data=archivo,
            file_name=f"vuelo_{icao_input}.kmz",
            mime="application/vnd.google-earth.kmz"
        )
    else:
        st.warning("Por favor ingresa un código ICAO24.")
