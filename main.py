import requests
import streamlit as st

def obtener_vuelo_historico(icao24, fecha_inicio, fecha_fin):
    # Convertimos fechas a timestamps UNIX (necesarios para la API)
    # ... (código de conversión de fecha a timestamp)
    
    url = "https://opensky-network.org/api/states/history"
    params = {
        'icao24': icao24,
        'begin': fecha_inicio_unix,
        'end': fecha_fin_unix
    }
    
    # Aquí usarías tus credenciales de OpenSky
    response = requests.get(url, params=params, auth=('TU_USUARIO', 'TU_CONTRASEÑA'))
    
    if response.status_code == 200:
        return response.json()
    else:
        return None
