import streamlit as st
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Flight Tracker App", layout="centered")

# --- BLOQUE 1: Configuración ---
with st.container(border=True):
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.write("⚙️") # Icono configuración
    with col2:
        st.subheader("Configurar Flightradar24")
        st.write("Conecta tu cuenta para buscar vuelos reales")

# --- BLOQUE 2: Mis Aeronaves ---
with st.container(border=True):
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.write("✈️") # Icono avión
    with col2:
        st.subheader("Mis Aeronaves")
        st.write("0 aeronaves registradas")

# --- BLOQUE 3: Flight Tracker ---
with st.container(border=True):
    st.subheader("✈️ Flight Tracker")
    
    # Inputs
    reg = st.text_input("Aircraft Registration", placeholder="e.g., N12345")
    date = st.date_input("Flight Date", value=None, format="DD/MM/YYYY")
    
    # Botón principal
    search_btn = st.button("🔍 Search Flight", use_container_width=True, type="primary")

# Lógica de respuesta
if search_btn:
    if reg and date:
        st.success(f"Buscando el vuelo {reg} para el día {date}...")
    else:
        st.error("Por favor completa ambos campos.")
