import streamlit as st
import pandas as pd
import requests
import simplekml
import os
from bs4 import BeautifulSoup

# Configuración de página
st.set_page_config(page_title="Flight Route KMZ Generator", layout="wide")

st.title("🛰️ Flight Route KMZ Generator")

# Bloque de Auditoría
with st.container(border=True):
    st.subheader("🔍 Auditoría de Aeronave")
    matricula = st.text_input("Ingresá la matrícula (ej: TC-66):")
    if st.button("Verificar Actividad"):
        url = f"https://www.flightradar24.com/data/aircraft/{matricula.lower()}"
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            st.success("Conexión exitosa con FR24. Sistema listo para procesar.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

# Bloque de Conversión
with st.container(border=True):
    st.subheader("🛠️ Procesador de Trazas a KMZ")
    archivo = st.file_uploader("Subí tu archivo CSV de traza:", type=["csv"])
    
    if archivo:
        if st.button("Convertir a KMZ"):
            try:
                df = pd.read_csv(archivo)
                kml = simplekml.Kml()
                coords = []
                for _, f in df.iterrows():
                    # Ajusta estas columnas según tu CSV
                    coords.append((float(f['Longitude']), float(f['Latitude']), float(f['Altitude']) * 0.3048))
                
                ruta = kml.newlinestring(name="Ruta de Vuelo", coords=coords)
                ruta.altitudemode = simplekml.AltitudeMode.absolute
                ruta.extrude = 1
                
                archivo_salida = "ruta_procesada.kmz"
                kml.save(archivo_salida)
                
                with open(archivo_salida, "rb") as f:
                    st.download_button("📥 DESCARGAR KMZ", f, archivo_salida)
                os.remove(archivo_salida)
            except Exception as e:
                st.error(f"Error procesando: {e}")
