import requests
import simplekml
from io import BytesIO

API_KEY = 'tu_api_key'
BASE_URL = 'https://api.flightradar24.com/...'  # URL real de la API

def obtener_vuelos_por_fecha(matricula, fecha):
    url = f"{BASE_URL}/flights?registration={matricula}&date={fecha}"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()  # lista de vuelos ese día

def obtener_traza_vuelo(flight_id):
    url = f"{BASE_URL}/flight/{flight_id}/route"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()  # lista de puntos latlonalt

def crear_kmz(ruta_puntos):
    kml = simplekml.Kml()
    coords = [(p['lon'], p['lat'], p['alt']) for p in ruta_puntos]
    ls = kml.newlinestring(name="Ruta de Vuelo", coords=coords)
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.extrude = 1
    kmz_io = BytesIO()
    kml.savekmz(kmz_io)
    kmz_io.seek(0)
    return kmz_io

# Ejemplo de uso
matricula = "N12345"
fecha = "2024-06-12"

vuelos = obtener_vuelos_por_fecha(matricula, fecha)
if vuelos:
    vuelo_id = vuelos[0]['id']
    traza = obtener_traza_vuelo(vuelo_id)
    kmz_file = crear_kmz(traza)
    # Aquí guardas el archivo o lo envías al usuario
else:
    print("No se encontraron vuelos para esa aeronave en esa fecha.")
