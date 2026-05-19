import streamlit as st
import pandas as pd
import simplekml
import os

# Configuración del Dashboard
st.set_page_config(page_title="Flight Route KMZ Generator", layout="wide")

st.title("🛰️ Flight Route KMZ Generator")
st.markdown("---")

# --- PASO 1: CONFIGURACIÓN Y SELECCIÓN ---
st.sidebar.header("1. Configuración")
lista_aeronaves = ["TC-66 (Hércules)", "TC-61 (Hércules)", "LV-FQZ (B737)", "ZM421 (A400M)"]
aeronave = st.sidebar.selectbox("Seleccionar Aeronave:", lista_aeronaves)

# --- PASO 2: PROCESAMIENTO DE DATOS ---
st.header("2. Carga y Procesamiento")
archivo = st.file_uploader("Subí el archivo de traza (CSV):", type=["csv"])

if archivo:
    df = pd.read_csv(archivo)
    st.write("Datos cargados correctamente:")
    st.dataframe(df.head())
    
    # --- PASO 3: EXPORTACIÓN ---
    st.header("3. Generar KMZ")
    if st.button("Convertir a KMZ"):
        try:
            # Buscamos columnas de forma inteligente
            lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
            lon_col = next((c for c in df.columns if 'lon' in c.lower()), None)
            alt_col = next((c for c in df.columns if 'alt' in c.lower()), None)
            
            if not all([lat_col, lon_col, alt_col]):
                st.error("Error: No se encontraron columnas de Lat/Lon/Alt en el CSV.")
            else:
                coords = []
                for _, fila in df.iterrows():
                    coords.append((float(fila[lon_col]), float(fila[lat_col]), float(fila[alt_col]) * 0.3048))
                
                # Crear KML
                kml = simplekml.Kml()
                ruta = kml.newlinestring(name=f"Ruta {aeronave}", coords=coords)
                ruta.altitudemode = simplekml.AltitudeMode.absolute
                ruta.extrude = 1
                
                kml.save("ruta_procesada.kmz")
                
                with open("ruta_procesada.kmz", "rb") as f:
                    st.download_button("📥 DESCARGAR KMZ", f, f"{aeronave.replace(' ', '_')}.kmz")
                
                os.remove("ruta_procesada.kmz")
                st.success("¡Archivo generado con éxito!")
                
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")
