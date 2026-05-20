import streamlit as st
import requests
import simplekml
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Extractor GIS de Vuelos", layout="wide", page_icon="✈️")

# --- FUNCIONES AUXILIARES (Aisladas para evitar errores de sintaxis) ---
def consultar_api_radares(matricula, fecha_str):
    """Hace la petición a la API y maneja errores de conexión."""
    url = f"https://api.airplanes.live/v2/historical/{matricula}/{fecha_str}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            return None, f"❌ No se encontraron datos para la matrícula {matricula} en la fecha {fecha_str}."
        else:
            return None, f"❌ Error de servidor (Código {response.status_code})."
    except requests.exceptions.Timeout:
        return None, "❌ La conexión con el servidor de radares tardó demasiado."
    except Exception as e:
        return None, f"❌ Ocurrió un error inesperado de red: {e}"

def generar_kmz_aeronautico(matricula, fecha_str, puntos_radar):
    """Procesa los puntos y construye el archivo KMZ estructurado para QGIS."""
    coordenadas_validas = []
    tiempos = []
    
    for p in puntos_radar:
        # Estructura: p[0]= timestamp, p[1]= lat, p[2]= lon, p[3]= altitud
        timestamp = p[0]
        lat = p[1]
        lon = p[2]
        alt = p[3] if p[3] is not None and p[3] != "ground" else 0
        
        if lat is not None and lon is not None:
            coordenadas_validas.append((lat, lon, alt))
            hora_legible = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            tiempos.append(hora_legible)
            
    if not coordenadas_validas:
        return None, None, None

    kml = simplekml.Kml()
    
    # 1. Crear línea continua de la trayectoria
    linea = kml.newlinestring(name=f"Ruta_{matricula}_{fecha_str}")
    linea.coords = [(c[1], c[0], c[2]) for c in coordenadas_validas]
    linea.style.linestyle.color = "ff00ff00"  # Verde brillante en formato KML
    linea.style.linestyle.width = 4
    linea.altitudemode = simplekml.AltitudeMode.absolute
    
    # 2. Crear puntos individuales con marcas de tiempo para la tabla de atributos de QGIS
    for coord, hora in zip(coordenadas_validas, tiempos):
        pnto = kml.newpoint(name=hora)
        pnto.coords = [(coord[1], coord[0], coord[2])]
        pnto.description = f"Hora: {hora} | Altitud: {coord[2]} ft"
        pnto.altitudemode = simplekml.AltitudeMode.absolute
        
    buffer_kmz = BytesIO()
    kml.savekmz(buffer_kmz)
    buffer_kmz.seek(0)
    
    return buffer_kmz, tiempos[0], tiempos[-1]


# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("✈️ Extractor de Trayectorias para QGIS")
st.markdown("Carga la matrícula de cualquier aeronave (civil o militar) y descarga el recorrido exacto de un día específico.")

col1, col2 = st.columns(2)
with col1:
    matricula = st.text_input("Matrícula de la aeronave (ej: VPFAZ o 944)", value="VPFAZ").strip().upper().replace("-", "")
with col2:
    fecha = st.date_input("Fecha a consultar", value=datetime.today())

st.markdown("---")

if st.button("🔍 Extraer Recorrido del Día", type="primary"):
    with st.spinner("Buscando en la base de datos de antenas comunitarias..."):
        fecha_str = fecha.strftime("%Y-%m-%d")
        
        # Llamamos a la función de red
        data, error_msg = consultar_api_radares(matricula, fecha_str)
        
        if error_msg:
            st.error(error_msg)
         Lido = False
        else:
            puntos_radar = data.get("trace", [])
            if not puntos_radar:
                st.warning(f"⚠️ La aeronave {matricula} existe, pero no emitió señales de radar el {fecha_str}.")
            else:
                # Llamamos a la función de generación geográfica
                buffer_kmz, hora_inicio, hora_fin = generar_kmz_aeronautico(matricula, fecha_str, puntos_radar)
                
                if not buffer_kmz:
                    st.warning("⚠️ Los datos recibidos no contenían coordenadas geográficas válidas.")
                else:
                    st.success(f"✅ ¡Recorrido encontrado! Se procesaron {len(puntos_radar)} registros de posición.")
                    st.info(f"⏱️ **Ventana de actividad registrada:** Desde las {hora_inicio} hasta las {hora_fin} (Hora UTC).")
                    
                    # Botón de descarga para el usuario
                    st.download_button(
                        label="💾 Descargar Archivo KMZ para QGIS",
                        data=buffer_kmz,
                        file_name=f"track_{matricula}_{fecha_str}.kmz",
                        mime="application/vnd.google-earth.kmz"
                    )
