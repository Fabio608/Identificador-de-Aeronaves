import streamlit as st
from FlightRadar24 import FlightRadar24API

# 1. Inicializar la API y la memoria de la aplicación
fr_api = FlightRadar24API()

if "trayectoria_lista" not in st.session_state:
    st.session_state.trayectoria_lista = None

st.title("🗺️ Buscador de Trayectorias")

# 2. Zona de Inputs (Formulario seguro)
# Usar un form agrupa los elementos y evita que la app intente recargarse a mitad de escritura
with st.form(key="buscador_vuelo"):
    codigo_vuelo = st.text_input("Código de vuelo (ej. AR1300):")
    boton_buscar = st.form_submit_button(label="Buscar Trayectoria")

# 3. Zona de Procesamiento (Solo guarda datos, no dibuja nada complejo aún)
if boton_buscar and codigo_vuelo:
    with st.spinner("Conectando con el playback de Flightradar24..."):
        try:
            # Reemplazá esto por tu lógica real de búsqueda de vuelos
            vuelos = fr_api.get_flights(aircraft_type=codigo_vuelo) 
            
            if vuelos:
                # Simulamos que tomamos el primer vuelo encontrado para extraer su trail
                detalles = fr_api.get_flight_details(vuelos[0].id)
                
                # Guardamos los datos puros en la memoria de la sesión
                st.session_state.trayectoria_lista = detalles.get('trail', [])
            else:
                st.warning("No se encontraron vuelos históricos recientes con ese código.")
                st.session_state.trayectoria_lista = None
        except Exception as e:
            st.error(f"Error de conexión: {e}")

---

# 4. Zona de Renderizado Seguro (Fuera del botón, libre de glitches de JavaScript)
if st.session_state.trayectoria_lista:
    st.success("¡Datos recuperados con éxito!")
    
    # Extraemos las coordenadas de manera limpia
    latitudes = [punto['lat'] for punto in st.session_state.trayectoria_lista]
    longitudes = [punto['lng'] for punto in st.session_state.trayectoria_lista]
    
    # Dibujamos de forma nativa y segura
    import pandas as pd
    df_mapa = pd.DataFrame({'lat': latitudes, 'lon': longitudes})
    
    st.subheader("Visualización del trayecto")
    st.map(df_mapa)
