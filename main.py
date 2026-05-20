import streamlit as st
import pandas as pd
# ... (mantén tus otros imports y funciones)

def procesar_vuelos(states):
    """
    Toma la lista de estados y los agrupa en vuelos basados en pausas de tiempo.
    """
    if not states:
        return []
    
    # Convertimos a DataFrame para facilitar el análisis
    df = pd.DataFrame(states, columns=['icao24', 'callsign', 'origin_country', 'time_position', 
                                       'last_contact', 'longitude', 'latitude', 'baro_altitude', 
                                       'on_ground', 'velocity', 'true_track', 'vertical_rate', 
                                       'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'])
    
    # Ordenamos por tiempo
    df = df.sort_values(by='time_position')
    
    # Detectamos pausas: si la diferencia entre un dato y otro es > 1800 seg (30 min)
    df['pausa'] = df['time_position'].diff() > 1800
    df['num_vuelo'] = df['pausa'].cumsum()
    
    vuelos = []
    for num, group in df.groupby('num_vuelo'):
        vuelos.append(group[['latitude', 'longitude', 'baro_altitude']].values.tolist())
    
    return vuelos

# --- Dentro de tu botón "Buscar en OpenSky" ---
if st.button("Buscar en OpenSky"):
    # ... (tu llamada a buscar_vuelos_opensky)
    
    if resultado and 'states' in resultado and resultado['states']:
        lista_vuelos = procesar_vuelos(resultado['states'])
        st.success(f"✅ Se detectaron {len(lista_vuelos)} vuelos distintos.")
        
        for idx, coords in enumerate(lista_vuelos):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"✈️ Vuelo {idx + 1}: {len(coords)} puntos de traza registrados.")
            with col2:
                archivo = generar_kmz(f"Vuelo_{idx+1}", coords)
                st.download_button(
                    label="Descargar KMZ",
                    data=archivo,
                    file_name=f"vuelo_{idx+1}.kmz",
                    key=f"dl_{idx}"
                )
            st.divider()
