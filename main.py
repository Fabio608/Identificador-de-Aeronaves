import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import time

# --- Configuración de Firebase ---
if not firebase_admin._apps:
    # Asegúrate de tener el archivo JSON en la misma carpeta
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Configuración de la Página ---
st.set_page_config(page_title="Flight Tracker", layout="centered")

# --- Funciones de Lógica ---
def get_flights(reg):
    # Simulación de llamada a tu API backend
    # response = requests.get(f"https://tu-api.com/flights/{reg}")
    # return response.json().get('flights', [])
    return [{"id": "FL1", "flightNumber": "AR1234", "origin": "EZE", "destination": "CRV", "status": "En Vuelo"}]

# --- Interfaz ---
st.title("✈️ Flight Tracker")
st.markdown("### Telemetry Engine")

# Gestión de Configuración (SideBar)
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Flightradar24 API Key", type="password")
    if st.button("Guardar API Key"):
        db.collection("configs").document("user_global").set({"apiKey": api_key})
        st.success("API Key guardada en Firestore")

# Sección principal
reg_input = st.text_input("Aircraft Registration", placeholder="e.g., N12345").upper()
date_input = st.date_input("Flight Date")

if st.button("Initialize Search"):
    if reg_input:
        with st.spinner('Consultando base de datos...'):
            flights = get_flights(reg_input)
            if flights:
                for f in flights:
                    with st.container(border=True):
                        st.write(f"**Vuelo:** {f['flightNumber']} | **Ruta:** {f['origin']} -> {f['destination']}")
                        st.caption(f"Estado: {f['status']}")
                        if st.button(f"Descargar KML", key=f['id']):
                            time.sleep(1) # Simulación de procesamiento
                            st.success(f"Archivo generado para {f['id']}")
            else:
                st.error("No se encontraron vuelos.")
    else:
        st.warning("Por favor ingresa una matrícula.")

# Gestión de Aeronaves (Base de datos)
st.divider()
st.subheader("Mis Aeronaves")
new_reg = st.text_input("Agregar nueva matrícula", key="new_reg")
if st.button("Registrar en Firestore"):
    db.collection("aircraft").add({"registration": new_reg.upper(), "timestamp": firestore.SERVER_TIMESTAMP})
    st.rerun()

# Listado desde Firestore
st.write("Aeronaves guardadas:")
aircraft_ref = db.collection("aircraft").stream()
for ac in aircraft_ref:
    st.text(f"• {ac.to_dict().get('registration')}")
