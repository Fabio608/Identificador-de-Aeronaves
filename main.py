import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestor de Flota Aeronáutica", layout="wide")

# 1. Base de datos de tus aeronaves (La lista que querés controlar)
# Podés agregar todas las que quieras acá
FLOTA = {
    "TC-66": "Hércules C-130H (Militar)",
    "TC-61": "Hércules C-130H (Militar)",
    "LV-FQZ": "B737 (Civil)",
    "LV-GVC": "B737 (Civil)"
}

st.title("✈️ Gestor de Flota Aeronáutica")

# Navegación
opcion = st.sidebar.radio("Sección:", ["Mis Aeronaves", "Auditoría de Historial", "Carga de Datos"])

if opcion == "Mis Aeronaves":
    st.header("Flota bajo seguimiento")
    df_flota = pd.DataFrame.from_dict(FLOTA, orient='index', columns=['Tipo'])
    st.table(df_flota)
    
    nueva_mat = st.text_input("Agregar nueva matrícula:")
    if st.button("Guardar"):
        st.success(f"Aeronave {nueva_mat} agregada al registro.")

elif opcion == "Auditoría de Historial":
    st.header("Historial de Vuelos")
    mat_seleccionada = st.selectbox("Elegir aeronave:", list(FLOTA.keys()))
    
    st.info(f"Mostrando vuelos históricos para: {mat_seleccionada}")
    # Aquí es donde pondríamos la lógica de consulta a tu base de datos local
    st.write("Cargando registros descargados...")

elif opcion == "Carga de Datos":
    st.header("Ingreso de nuevas trazas")
    mat = st.selectbox("¿A qué aeronave pertenece el vuelo?", list(FLOTA.keys()))
    archivo = st.file_uploader("Subir KMZ/CSV de FR24", type=["kmz", "csv"])
    
    if archivo:
        # Aquí procesamos el archivo y lo guardamos con un nombre inteligente
        # por ejemplo: /data/TC-66/2026-05-19_vuelo.kmz
        st.success(f"Archivo de {mat} procesado y guardado en la base de datos.")
