import streamlit as st
import requests
import simplekml
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Extractor GIS de Vuelos", layout="wide", page_icon="✈️")

st.title("✈️ Extractor de Trayectorias para QGIS")
st.markdown("Carga la matrícula de cualquier aeronave (civil o militar) y descarga el recorrido exacto de un día específico.")

# --- FORMULARIO DE BÚSQUEDA ---
col1, col2 = st.columns(2)
with col1:
    matricula = st.text_input("Matrícula de la aeronave (ej: VPFAZ o 944)", value="VPFAZ").strip().upper().replace("-", "")
with col2:
    fecha = st.date_input("Fecha a consultar", value=datetime.today())

st.markdown("---")

# --- BOTÓN DE ACCIÓN ---
if st.button("🔍 Extraer Recorrido del Día", type="primary"):
    with st.spinner("Buscando en la base de datos de antenas comunitarias..."):
        
        fecha_str = fecha.strftime("%Y-%m-%d")
        url = f"https://api.airplanes.live/v2/historical/{matricula}/{fecha_str}"
        
        try:
            response = requests.get(url, timeout=15)
            
            if response.status_code == 404:
                st.error(f"❌ No se encontraron datos para la matrícula {matricula} en la fecha {fecha_str}.")
            elif response.status_code != 200:
                st.error(f"❌ Error de servidor (Código {response.status_code}). Intenta de nuevo en unos minutos.")
            else:
                data = response.json()
                puntos_radar = data.get("trace", [])
                
                if not puntos_radar:
                    st.warning(f"⚠️ La aeronave {matricula} existe, pero no emitió señales de radar el {fecha_str}.")
                else:
                    coordenadas_validas = []
                    tiempos = []
                    
                    for p in puntos_radar:
                        timestamp = p[0]
                        lat = p[1]
                        lon = p[2]
                        alt = p[3] if p[3] is not None and p[3] != "ground" else 0
                        
                        if lat is not None and lon is not None:
                            coordenadas_validas.append((lat, lon, alt))
                            hora_legible = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                            tiempos.append(hora_legible)
                    
                    # --- MOSTRAR RESULTADOS ---
                    st.success(f"✅ ¡Recorrido encontrado! Se procesaron {len(coordenadas_validas)} puntos de posicionamiento.")
                    
                    # Datos estadísticos rápidos del vuelo (Corregido para evitar SyntaxError)
                    hora_inicio = tiempos[0]
                    hora_fin = tiempos[-1]
                    texto_info = f"⏱️ Ventana de actividad registrada: Desde las {hora_inicio} hasta las {hora_fin} (Hora UTC)."
                    st.info(texto_info)
                    
                    # --- GENERAR EL ARCHIVO KMZ ---
                    kml = simplekml.Kml()
                    
                    # 1. Creamos la línea continua de la ruta
                    linea = kml.newlinestring(name=f"Ruta_{matricula}_{fecha_str}")
                    linea.coords = [(c[1], c[0], c[2]) for c in coordenadas_validas]
                    linea.style.linestyle.color = "ff00ff00"  # Verde brillante
