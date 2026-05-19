import streamlit as st
import pandas as pd
import requests
import os
import simplekml
from bs4 import BeautifulSoup

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
                
                for fila in filas:
                    celdas = fila.find_all("td")
                    if len(celdas) > 5:
                        fecha = celdas[2].text.strip()
                        ruta = f"{celdas[3].text.strip()} ➡️ {celdas[4].text.strip()}"
                        f_id = fila.get("data-playback")
                        
                        st.write(f"📅 **{fecha}** | {ruta}")
                        if f_id:
                            link = f"https://www.flightradar24.com/data/aircraft/{matricula.lower()}#{f_id}"
                            st.link_button("Ir al Playback", link)
            except Exception as e:
                st.error(f"Error técnico: {e}")

# --- MÓDULO 2: PROCESADOR ---
elif modulo == "Procesador KMZ":
    st.subheader("Convertidor a KMZ profesional")
    archivo = st.file_uploader("Subir archivo CSV de traza:", type=["csv"])
    
    if archivo:
        try:
            df = pd.read_csv(archivo)
            # Intentamos detectar columnas comunes
            lat_col = [c for c in df.columns if 'lat' in c.lower()][0]
            lon_col = [c for c in df.columns if 'lon' in c.lower()][0]
            alt_col = [c for c in df.columns if 'alt' in c.lower()][0]
            
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
            
            kml.save("resultado.kmz")
            with open("resultado.kmz", "rb") as f:
                st.download_button("Descargar KMZ generado", f, "traza_procesada.kmz")
            os.remove("resultado.kmz")
            st.success("¡Archivo listo para Google Earth!")
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")
