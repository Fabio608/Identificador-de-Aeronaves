import streamlit as st
import simplekml
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="Flight Tracker", layout="wide")

st.title("✈️ Historial de Aeronaves")

# --- Base de datos simulada (En el futuro, esto vendrá de OpenSky/Firestore) ---
# Simulamos que la aeronave 944 realizó 3 vuelos hoy
vuelos_registrados = [
    {"id": "Vuelo 1", "fecha": "19/05/2026", "ruta": "SCTI -> SCBA", "coords": [(-45.85, -67.48, 5000), (-45.90, -67.55, 5100)]},
    {"id": "Vuelo 2", "fecha": "19/05/2026", "ruta": "SCBA -> SCBA", "coords": [(-45.90, -67.55, 5100), (-46.00, -67.60, 5200)]},
    {"id": "Vuelo 3", "fecha": "19/05/2026", "ruta": "SCBA -> SCTI", "coords": [(-46.00, -67.60, 5200), (-45.85, -67.48, 5000)]}
]

def generar_kmz(nombre, coordenadas):
    kml = simplekml.Kml()
    coords = [(p[1], p[0], p[2]) for p in coordenadas]
    lin = kml.newlinestring(name=f"Trayectoria {nombre}")
    lin.coords = coords
    buffer = BytesIO()
    kml.savekmz(buffer)
    buffer.seek(0)
    return buffer

# --- Interfaz ---
reg_input = st.text_input("Ingresa Registro (ej: 944)").strip()

if st.button("Consultar Historial"):
    if reg_input == "944":
        st.subheader(f"Resumen de vuelos para Twin Otter FACH (Reg: 944)")
        st.write(f"Se encontraron **{len(vuelos_registrados)}** vuelos el día 19/05/2026:")
        
        # Crear tabla visual
        for vuelo in vuelos_registrados:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{vuelo['id']}** ({vuelo['fecha']})")
            with col2:
                st.write(f"Ruta: {vuelo['ruta']}")
            with col3:
                # Botón de descarga para cada vuelo individual
                archivo = generar_kmz(vuelo['id'], vuelo['coords'])
                st.download_button(
                    label="Descargar KMZ",
                    data=archivo,
                    file_name=f"vuelo_{vuelo['id']}.kmz",
                    mime="application/vnd.google-earth.kmz",
                    key=vuelo['id'] # Llave única para cada botón
                )
            st.divider()
    else:
        st.error("No se encontraron registros para esa matrícula.")
