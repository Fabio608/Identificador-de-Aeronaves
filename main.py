import os
import re
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from datetime import datetime

# ============================================================
# CONFIG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Auditor de Actividad FR24",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Auditor de Actividad y Generador de Playback FR24")
st.markdown("""
Ingresá o seleccioná una aeronave y el sistema escaneará su historial completo reciente 
para mostrarte **qué días voló, qué rutas hizo** y darte el acceso directo a su Playback.
""")

# ============================================================
# LISTADO DE FAVORITOS
# ============================================================
AERONAVES_INTERES = {
    "TC-66 (Lockheed C-130H Hércules)": "tc-66",
    "TC-61 (Lockheed C-130H Hércules)": "tc-61",
    "LV-FQZ (Boeing 737 Aerolíneas)": "lv-fqz",
    "ZM421 (Airbus A400M RAF)": "zm421"
}

# ============================================================
# INTERFAZ DE USUARIO (PANEL IZQUIERDO)
# ============================================================
st.sidebar.header("🔍 Configuración del Monitoreo")

modo_seleccion = st.sidebar.radio("Objetivo:", ["Mis Favoritos", "Cargar Matrícula Manual"])

if modo_seleccion == "Mis Favoritos":
    nombre_comun = st.sidebar.selectbox("Seleccioná la aeronave:", list(AERONAVES_INTERES.keys()))
    matricula = AERONAVES_INTERES[nombre_comun]
else:
    matricula = st.sidebar.text_input("Ingresá la matrícula (Ej: TC-66, LV-FQZ):", "").strip().lower().replace(" ", "")

ejecutar = st.sidebar.button("🚀 Escanear Actividad Reciente", type="primary")

# ============================================================
# LOGICA DE EXTRACCIÓN (SCRAPING DE FR24)
# ============================================================
def escanear_historial_fr24(matricula_avion):
    url = f"https://www.flightradar24.com/data/aircraft/{matricula_avion}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9"
    }
    
    vuelos_encontrados = []
    
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 404:
            st.error("❌ La matrícula ingresada no existe en los registros de Flightradar24.")
            return None
        elif r.status_code != 200:
            st.error(f"⚠️ FR24 bloqueó la conexión temporalmente (Código {r.status_code}). Intentá de nuevo en unos minutos.")
            return None
            
        soup = BeautifulSoup(r.text, "html.parser")
        # Buscamos las filas de la tabla de vuelos en el HTML de la página
        filas_tabla = soup.find_all("tr", class_="data-row")
        
        for fila in filas_tabla:
            # Extracción de datos columna por columna seguro
            celdas = fila.find_all("td")
            if len(celdas) < 9:
                continue
                
            # 1. Fecha
            fecha_raw = celdas[2].text.strip() if celdas[2] else "Desconocida"
            
            # 2. Ruta (Origen -> Destino)
            origen = celdas[3].text.strip() if celdas[3] else "---"
            destino = celdas[4].text.strip() if celdas[4] else "---"
            # Limpieza de textos largos de aeropuertos
            origen = re.sub(r'\s+', ' ', origen)
            destino = re.sub(r'\s+', ' ', destino)
            
            # 3. Número de Vuelo / Callsign
            callsign = celdas[5].find("a").text.strip() if celdas[5].find("a") else (celdas[5].text.strip() if celdas[5] else "---")
            
            # 4. Estado (Aterrizó, Programado, Desconocido)
            estado = celdas[8].text.strip() if celdas[8] else "---"
            estado = re.sub(r'\s+', ' ', estado)
            
            # 5. ID de Playback de FR24 (Oculto en el atributo de la fila)
            flight_id = fila.get("data-playback", None)
            
            # Filtrar filas vacías o repetidas que usa FR24 para diseño dinámico
            if origen == "---" and destino == "---":
                continue
                
            vuelos_encontrados.append({
                "Fecha": fecha_raw,
                "Vuelo/Callsign": callsign,
                "Origen": origen,
                "Destino": destino,
                "Estado del Vuelo": estado,
                "flight_id": flight_id
            })
            
    except Exception as e:
        st.error(f"❌ Error al conectar con el servidor: {e}")
        return None
        
    return vuelos_encontrados

# ============================================================
# DESPLIEGUE DE RESULTADOS (PANEL CENTRAL)
# ============================================================
if ejecutar:
    if not matricula:
        st.warning("⚠️ Por favor, ingresá una matrícula válida en el panel izquierdo.")
    else:
        st.subheader(f"📊 Reporte de Actividad para: {matricula.upper()}")
        
        with st.spinner(f"Escaneando el historial web de {matricula.upper()}..."):
            historial = escanear_historial_fr24(matricula)
            
        if historial:
            # Convertimos la lista de datos a un formato de tabla limpio (Pandas Dataframe)
            df = pd.DataFrame(historial)
            
            st.success(f"🚨 ¡Análisis Completo! Se detectaron {len(df)} registros de actividad recientes.")
            
            # Mostramos la tabla general resumida para control rápido
            st.markdown("### 📅 Resumen de movimientos detectados:")
            st.dataframe(df[["Fecha", "Vuelo/Callsign", "Origen", "Destino", "Estado del Vuelo"]], use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🚀 Accesos Directos a Playback Confirmados:")
            st.info("Hacé clic en el botón del día que te interesa. Te abrirá Flightradar24 listo para reproducir y descargar el archivo con tu cuenta.")
            
            # Generamos botones dinámicos fila por fila
            for vuelo in historial:
                # Si el vuelo tiene un ID de reproducción válido, armamos el acceso directo
                if vuelo["flight_id"]:
                    link_playback = f"https://www.flightradar24.com/data/aircraft/{matricula}#{vuelo['flight_id']}"
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**🟢 {vuelo['Fecha']}** | Vuelo `{vuelo['Vuelo/Callsign']}` | `{vuelo['Origen']}` ➡️ `{vuelo['Destino']}` ({vuelo['Estado del Vuelo']})")
                    with col2:
                        st.link_button(f"🌐 Ver Playback ({vuelo['Fecha']})", link_playback, use_container_width=True)
                else:
                    # Vuelos futuros programados que todavía no tienen track de reproducción
                    st.markdown(f"**⚪ {vuelo['Fecha']}** | Vuelo `{vuelo['Vuelo/Callsign']}` | `{vuelo['Origen']}` ➡️ `{vuelo['Destino']}` (*{vuelo['Estado del Vuelo']}*)")
        else:
            st.warning("💤 No se encontraron registros de vuelo recientes para esta aeronave en la sección pública.")
