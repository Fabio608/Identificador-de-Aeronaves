import gzip
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def procesar_opensky_a_gpkg(ruta_csv_gz, icao24_buscado, ruta_salida_gpkg):
    """
    Lee un archivo masivo de OpenSky (.csv.gz), filtra por un ICAO24 específico
    y exporta los puntos ordenados cronológicamente a un GeoPackage listo para QGIS.
    """
    print(f"⏳ Abriendo y filtrando el archivo masivo para el ICAO24: {icao24_buscado}...")
    
    # 1. Definimos las columnas estándar de los State Vectors de OpenSky
    # Nota: Ajusta los nombres si el dataset mensual varía levemente de estructura
    columnas = [
        'time', 'icao24', 'lat', 'lon', 'velocity', 'heading', 'vertrate', 
        'callsign', 'onground', 'alert', 'spi', 'squawk', 'baroaltitude', 
        'geoaltitude', 'lastposupdate', 'lastcontact'
    ]
    
    chunks_filtrados = []
    
    # 2. Leemos por fragmentos (chunks) para no saturar la memoria RAM
    tamanio_chunk = 500_000
    try:
        for chunk in pd.read_csv(ruta_csv_gz, names=columnas, compression='gzip', chunksize=tamanio_chunk, low_memory=False):
            # Filtramos inmediatamente el fragmento por el avión que nos interesa
            df_filtro = chunk[chunk['icao24'].str.lower() == icao24_buscado.lower()]
            if not df_filtro.empty:
                chunks_filtrados.append(df_filtro)
                
        if not chunks_filtrados:
            print(f"❌ No se encontraron registros para el ICAO24 '{icao24_buscado}' en este archivo.")
            return
            
        # Concatonamos todos los fragmentos encontrados
        df_resultado = pd.concat(chunks_filtrados, ignore_index=True)
        
        # 3. Limpieza y Ordenamiento
        print("🧹 Limpiando y ordenando datos cronológicamente...")
        # Eliminamos registros que no tengan coordenadas válidas
        df_resultado = df_resultado.dropna(subset=['lat', 'lon'])
        # Ordenamos por la marca de tiempo (Unix Timestamp)
        df_resultado = df_resultado.sort_values(by='time')
        
        # Convertimos el timestamp de Unix a una fecha legible por humanos para QGIS
        df_resultado['fecha_hora'] = pd.to_datetime(df_resultado['time'], unit='s')
        
        # 4. Conversión a datos Geoespaciales (GeoPandas)
        print("🗺️ Creando geometrías 3D (Lat, Lon, Altitud)...")
        # Rellenamos altitudes nulas con 0 para que no falle la geometría 3D
        df_resultado['baroaltitude'] = df_resultado['baroaltitude'].fillna(0)
        
        # Creamos los puntos geométricos incluyendo la coordenada Z (Altitud)
        geometria = [
            Point(xy[0], xy[1], z) 
            for xy, z in zip(zip(df_resultado['lon'], df_resultado['lat']), df_resultado['baroaltitude'])
        ]
        
        # Creamos el GeoDataFrame especificando el sistema WGS 84 (EPSG:4326)
        gdf = gpd.GeoDataFrame(df_resultado, geometry=geometria, crs="EPSG:4326")
        
        # Eliminamos la columna 'time' original o la dejamos como entero para evitar conflictos de tipos
        gdf['time'] = gdf['time'].astype(int)
        # Convertimos fecha_hora a string para máxima compatibilidad al guardar en GPKG
        gdf['fecha_hora'] = gdf['fecha_hora'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 5. Exportación
        print(f"💾 Guardando {len(gdf)} puntos en: {ruta_salida_gpkg}...")
        gdf.to_file(ruta_salida_gpkg, layer='puntos_vuelo', driver="GPKG")
        print("🚀 ¡Proceso completado con éxito! Ya podés arrastrar el archivo a QGIS.")
        
    except Exception as e:
        print(f"❌ Ocurrió un error durante el procesamiento: {e}")

# --- EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    # CONFIGURA TUS RUTAS AQUÍ:
    RUTA_ENTRADA = "datos_opensky_del_dia.csv.gz"  # Archivo original bajado de OpenSky
    ICAO24_AVION = "e80234"                        # El código HEX de la aeronave
    RUTA_SALIDA = "trayectoria_fach_944.gpkg"       # El archivo que vas a abrir en QGIS
    
    # Ejecutar
    procesar_opensky_a_gpkg(RUTA_ENTRADA, ICAO24_AVION, RUTA_SALIDA)
