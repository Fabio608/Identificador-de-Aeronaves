import os
import json
import requests
import simplekml
from datetime import datetime, timedelta

URL_HISTORIAL_BASE = "https://adsb.fi/history"
FICHERO_VIGILANCIA = "vigilancia.json"

def obtener_fecha_ayer():
    ayer = datetime.now() - timedelta(days=1)
    return ayer.strftime("%Y-%m-%d")

def cargar_lista_vigilancia():
    try:
        with open(FICHERO_VIGILANCIA, "r") as f:
            return json.load(f).get("aviones_vip", {})
    except FileNotFoundError:
        # Crea un archivo base si no existe
        ejemplo = {"aviones_vip": {"34612a": "Aeronave de Prueba"}}
        with open(FICHERO_VIGILANCIA, "w") as f:
            json.dump(ejemplo, f, indent=4)
        print(f"⚠️ Se creó '{FICHERO_VIGILANCIA}' de ejemplo. Editalo con tus códigos HEX.")
        return ejemplo["aviones_vip"]

def exportar_a_kmz(hex_code, descripcion, puntos_vuelo, fecha_str):
    kml = simplekml.Kml()
    coordenadas = []
    
    for p in puntos_vuelo:
        try:
            lat, lon, alt_pies = p[0], p[1], p[2]
            alt_metros = 0 if alt_pies == "ground" or not alt_pies else int(alt_pies) * 0.3048
            coordenadas.append((lon, lat, alt_metros))
        except (IndexError, ValueError):
            continue

    if not coordenadas:
        return

    ruta = kml.newlinestring(name=f"Vuelo {hex_code} - {descripcion}")
    ruta.coords = coordenadas
    ruta.extrude = 1 
    ruta.altitudemode = simplekml.AltitudeMode.absolute
    ruta.style.linestyle.color = simplekml.Color.red  
    ruta.style.linestyle.width = 4
    
    marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
    marcador.description = f"Avión: {descripcion}\nHEX: {hex_code}\nFecha: {fecha_str}"

    nombre_kmz = f"traza_{hex_code}_{fecha_str}.kmz"
    kml.savekmz(nombre_kmz)
    print(f"📦 [DESCARGA LISTA] Se generó el archivo: {os.path.abspath(nombre_kmz)}")

def ejecutar_analizador_historico():
    fecha_ayer = obtener_fecha_ayer()
    aviones_a_buscar = cargar_lista_vigilancia()
    
    if not aviones_a_buscar:
        print("⚠️ No hay aviones configurados. Abortando.")
        return
        
    print(f"🛰️ [INICIANDO] Buscando actividad del día anterior ({fecha_ayer})...")
    vuelos_totales_detectados = 0
    
    for hex_code, descripcion in aviones_a_buscar.items():
        hex_code = hex_code.lower().strip()
        dos_primeros = hex_code[:2]
        url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{hex_code}.json"
        
        try:
            respuesta = requests.get(url_peticion, timeout=15)
            if respuesta.status_code == 200:
                puntos = respuesta.json().get("trace", [])
                if len(puntos) >= 5:
                    vuelos_totales_detectados += 1
                    print(f"🚨 ¡ALERTA! Se detectó movimiento de: {descripcion} [{hex_code.upper()}]")
                    exportar_a_kmz(hex_code, descripcion, puntos, fecha_ayer)
            elif respuesta.status_code != 404:
                print(f"⚠️ Error con {descripcion} ({hex_code}): Código {respuesta.status_code}")
        except Exception as e:
            print(f"❌ Error procesando {hex_code}: {e}")
            
    if vuelos_totales_detectados == 0:
        print(f"💤 Ninguno de tus aviones listados voló ayer ({fecha_ayer}).")

if __name__ == "__main__":
    ejecutar_analizador_historico()
