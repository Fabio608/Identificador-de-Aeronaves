import requests
import json
import simplekml
from datetime import datetime, timedelta

# CONFIGURACIÓN DE LA API HISTÓRICA LIBRE
URL_HISTORIAL_BASE = "https://adsb.fi" 
FICHERO_VIGILANCIA = "vigilancia.json"

# 1. CALCULAR FECHA AUTOMÁTICAMENTE
def obtener_fecha_ayer():
    """Calcula automáticamente la fecha del día anterior en formato YYYY-MM-DD"""
    ayer = datetime.now() - timedelta(days=1)
    return ayer.strftime("%Y-%m-%d")

# 2. CARGAR LISTA DE VIGILANCIA
def cargar_lista_vigilancia():
    """Lee el archivo JSON local con las aeronaves a buscar"""
    try:
        with open(FICHERO_VIGILANCIA, "r") as f:
            return json.load(f).get("aviones_vip", {})
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{FICHERO_VIGILANCIA}' en esta carpeta.")
        return {}

# 3. GENERAR ARCHIVO KMZ COMPRIMIDO
def exportar_a_kmz(hex_code, descripcion, puntos_vuelo, fecha_str):
    """Toma los vectores de posición históricos y exporta un archivo .kmz tridimensional"""
    kml = simplekml.Kml()
    coordenadas = []
    
    # Procesamos cada punto del vector
    for p in puntos_vuelo:
        # Convertimos pies (alt_baro) a metros (multiplicando por 0.3048) para Google Earth
        alt_pies = p.get("alt_baro", 0)
        # Si alt_baro viene como texto o 'ground', lo manejamos como 0
        if isinstance(alt_pies, str):
            alt_metros = 0
        else:
            alt_metros = int(alt_pies) * 0.3048 if alt_pies else 0
            
        # El formato requerido por KML es: (Longitud, Latitud, Altitud en metros)
        coordenadas.append((p["lon"], p["lat"], alt_metros))
    
    # Creamos la línea de la traza de vuelo en el mapa
    ruta = kml.newlinestring(name=f"Vuelo {hex_code} - {descripcion}")
    ruta.coords = coordenadas
    ruta.extrude = 1 # Dibuja una 'pared' transparente desde el suelo hasta el avión
    ruta.altitudemode = simplekml.AltitudeMode.absolute
    ruta.style.linestyle.color = simplekml.Color.red # Línea de color rojo militar
    ruta.style.linestyle.width = 4 # Grosor de la línea
    
    # Marcador de inicio de la traza
    punto_inicial = puntos_vuelo[0]
    alt_ini_metros = (int(punto_inicial.get("alt_baro", 0)) * 0.3048) if isinstance(punto_inicial.get("alt_baro"), int) else 0
    marcador = kml.newpoint(name="Inicio de Traza Detectada", coords=[(punto_inicial["lon"], punto_inicial["lat"], alt_ini_metros)])
    marcador.description = f"Avión: {descripcion}\nCódigo HEX: {hex_code}\nFecha: {fecha_str}"

    # Guardado físico en el disco duro
    nombre_kmz = f"traza_{hex_code}_{fecha_str}.kmz"
    kml.savekmz(nombre_kmz)
    print(f"📦 [DESCARGA LISTA] Se generó el archivo: {nombre_kmz}")

# 4. PROCESAR HISTORIAL Y FILTRAR VECTORES
def ejecutar_analizador_historico():
    fecha_ayer = obtener_fecha_ayer()
    aviones_a_buscar = cargar_lista_vigilancia()
    
    if not aviones_a_buscar:
        print("⚠️ No hay aviones configurados en la lista de vigilancia. Abortando.")
        return
        
    print(f"🛰️ [INICIANDO CHEQUEO] Buscando actividad del día de ayer ({fecha_ayer})...")
    print(f"📋 Objetivos cargados para revisión: {list(aviones_a_buscar.values())}")
    
    # URL de descarga del registro histórico del día anterior
    url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}.json"
    
    try:
        # Hacemos la consulta a los servidores históricos libres
        print("🌐 Conectando con el servidor de registros históricos (esto puede demorar unos segundos)...")
        respuesta = requests.get(url_peticion, timeout=60)
        
        if respuesta.status_code != 200:
            print(f"❌ Error: El servidor no tiene disponible el historial del día {fecha_ayer} (Código: {respuesta.status_code}).")
            return
            
        datos_globales = respuesta.json().get("aircraft", [])
        print(f"📊 Datos del día descargados. Analizando posiciones globales...")
        
        # Diccionario temporal para agrupar los puntos geográficos de nuestros aviones de interés
        rutas_encontradas = {hex_id: [] for hex_id in aviones_a_buscar}
        
        # Recorremos el registro histórico buscando coincidencias con nuestra lista
        for registro in datos_globales:
            hex_registro = registro.get("hex")
            if hex_registro in aviones_a_buscar:
                # Validamos que el punto contenga coordenadas de vector válidas
                if registro.get("lat") and registro.get("lon"):
                    rutas_encontradas[hex_registro].append(registro)
                    
        # Verificamos cuáles aviones sí tuvieron vuelos y exportamos su KMZ
        vuelos_totales_detectados = 0
        for hex_code, puntos in rutas_encontradas.items():
            # Exigimos un mínimo de 5 puntos para asegurar que sea una traza con movimiento real
            if len(puntos) >= 5:
                vuelos_totales_detectados += 1
                descripcion = aviones_a_buscar[hex_code]
                print(f"🚨 ¡ALERTA! Se detectó movimiento de: {descripcion} [{hex_code}] (Registró {len(puntos)} posiciones).")
                exportar_a_kmz(hex_code, descripcion, puntos, fecha_ayer)
                
        if vuelos_totales_detectados == 0:
            print(f"💤 Chequeo finalizado: Ninguno de tus aviones listados voló el día de ayer ({fecha_ayer}).")
        else:
            print(f"✨ Proceso terminado. Se encontraron un total de {vuelos_totales_detectados} vuelos.")
            
    except requests.exceptions.Timeout:
        print("❌ Error: Se agotó el tiempo de espera al conectar con el servidor de la API.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado durante el análisis: {e}")

# Ejecutar el programa al abrir el archivo
if __name__ == "__main__":
    ejecutar_analizador_historico()
