import streamlit as st
import pandas as pd
import simplekml
import os

st.set_page_config(page_title="Flight Route KMZ", layout="centered")
st.title("🛰️ Flight Route KMZ Generator")

# Flujo simplificado: solo subida y conversión para evitar errores de navegación
st.subheader("Procesador de Traza (CSV a KMZ)")
archivo = st.file_uploader("Subí tu archivo CSV de Flightradar24:", type=["csv"])

if archivo:
    try:
        df = pd.read_csv(archivo)
        # Búsqueda inteligente de columnas (sin importar el nombre exacto)
        cols = {c.lower(): c for c in df.columns}
        lat_col = next((cols[c] for c in cols if 'lat' in c), None)
        lon_col = next((cols[c] for c in cols if 'lon' in c), None)
        alt_col = next((cols[c] for c in cols if 'alt' in c), None)

        if not all([lat_col, lon_col, alt_col]):
            st.error(f"No pude encontrar las columnas. Columnas halladas: {list(df.columns)}")
        else:
            if st.button("Generar KMZ"):
                coords = []
                for _, fila in df.iterrows():
                    # Conversión segura
                    lat = float(fila[lat_col])
                    lon = float(fila[lon_col])
                    alt = float(fila[alt_col]) * 0.3048
                    coords.append((lon, lat, alt))
                
                kml = simplekml.Kml()
                line = kml.newlinestring(name="Ruta", coords=coords)
                line.altitudemode = simplekml.AltitudeMode.absolute
                line.extrude = 1
                
                kml.save("resultado.kmz")
                with open("resultado.kmz", "rb") as f:
                    st.download_button("📥 DESCARGAR KMZ", f, "ruta.kmz")
                os.remove("resultado.kmz")
                st.success("¡Archivo listo!")
    except Exception as e:
        st.error(f"Error procesando: {e}")
