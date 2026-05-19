import os
import re
import requests
import simplekml
import streamlit as st
from datetime import datetime, timedelta

# ============================================================
# CONFIG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="FR24 → KMZ Histórico",
    page_icon="🛩️",
    layout="centered"
)

st.title("🛩️ Generador KMZ desde enlace FR24")
st.markdown("""
Pegá un enlace de Flightradar24 y el sistema extraerá la matrícula, 
buscará su historial de vuelo completo en la red comunitaria y generará el archivo KMZ.
""")

# ============================================================
# CONFIGURACIÓN DE APIs
# ============================================================
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
URL_BUSCADOR_HEX = "https://api.adsb.one/v2/registration"
URL_HISTORIAL_BASE = "https://adsb.fi/history"

# ============================================================
# FUNCIONES
# ============================================================

def extraer_datos_fr24(url):
    """ Extrae matrícula limpia desde cualquier variante de URL de FR24 """
    resultado = {"matricula": None}
    try:
        # Detecta la matrícula ignorando lo que haya antes o después (ej: /aircraft/tc-66#3fc194d1 o /data/aircraft/lv-fqz)
        match = re.search(r"aircraft/([a-zA-Z0-9\-]+)", url.lower())
        if match:
            resultado["matricula"] = match.group(1).strip().replace("-", "")
    except:
        pass
    return resultado

def obtener_hex(matricula):
    """ Traduce matrícula → HEX usando API en vivo y machete de emergencia """
    # Diccionario de rescate para asegurar códigos conflictivos o nuevos
    machete_militar = {
        "tc66": "e20094",  # Código nuevo confirmado por FlightRadar24
        "tc61": "e0224b",
        "tc64": "e0224d",
        "tc69": "e02250",
        "tc100": "e01862",
        "zm421": "43c5ef_r"
    }
    
    if matricula in machete_militar:
        return machete_militar[matricula]

    try:
        url = f"{URL_BUSCADOR_HEX}/{matricula}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "ac" in data and len(data["ac"]) > 0:
                return data["ac"][0].get("hex", "").lower().strip()
    except:
        pass
    return None

def obtener_traza_historica(hex_code, fecha_str):
    """ Descarga el archivo de traza histórica completo de un día específico """
    try:
        dos_primeros = hex_code[:2]
        url = f"{URL_HISTORIAL_BASE}/{fecha_str}/traces/{dos_primeros}/{hex_code}.json"
        
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json().get("trace", [])
    except:
        pass
    return []

def generar_kmz(coords, nombre):
    """ Construye el empaquetado binario KMZ para Google Earth """
    kml = simplekml.Kml()
    ruta = kml.newlinestring(name=nombre)
    ruta.coords = coords
    ruta.style.linestyle.color = simplekml.Color.red
    ruta.style.linestyle.width = 4
    ruta.altitudemode = simplekml.AltitudeMode.absolute
    ruta.extrude = 1

    # Marcador en el punto de partida
    marcador = kml.newpoint(name="Inicio de Ruta", coords=[coords[0]])

    archivo = "traza_temp.kmz"
    kml.savekmz(archivo)
    with open(archivo, "rb") as f:
        data = f.read()
    os.remove(archivo)
    return data

# ============================================================
# INTERFAZ DE USUARIO (INPUTS)
# ============================================================
st.subheader("🔍 1. Configurar Extracción")

url_ingresada = st.text_input(
    "Pegá el link de FR24 de la aeronave:",
    placeholder="Ej: https://www.flightradar24.com/data/aircraft/tc-66"
)

# Añadimos selector de fecha porque los archivos históricos se organizan por día cerrado
fecha_por_defecto = datetime.now() - timedelta(days=1)
fecha_seleccionada = st.date_input("Seleccioná la fecha del vuelo que querés procesar:", fecha_por_defecto)

# ============================================================
# PROCESAMIENTO
# ============================================================
if st.button("🚀 Procesar Enlace y Generar KMZ", type="primary"):
    if not url_ingresada:
        st.warning("⚠️ Por favor, pegá un enlace primero.")
        st.stop()

    # 1. Extraer datos de la URL
    datos = extraer_datos_fr24(url_ingresada)
    matricula = datos["matricula"]

    if not matricula:
        st.error("❌ No se pudo detectar una matrícula válida en el formato de la URL provista.")
        st.stop()

    st.success(f"✔️ Matrícula detectada en link: **{matricula.upper()}**")
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")

    # 2. Buscar Identificador HEX
    with st.spinner("Traduciendo matrícula a identificador de transpondedor HEX..."):
        hex_code = obtener_hex(matricula)

    if not hex_code:
        st.error(f"❌ No se encontró un código HEX asociado a la matrícula {matricula.upper()} en los registros públicos.")
        st.stop()

    st.info(f"🛰️ Identidad confirmada: Código HEX **[{hex_code.upper()}]**")

    # 3. Buscar Traza Histórica
    with st.spinner(f"Descargando historial de posiciones para el día {fecha_str}..."):
        puntos = obtener_traza_historica(hex_code, fecha_str)

    if not puntos or len(puntos) < 5:
        st.error(f"❌ **Sin novedades históricas:** No hay suficientes posiciones grabadas para el HEX {hex_code.upper()} el día {fecha_str}. Recordá que en zonas como Bolivia puede haber puntos ciegos de cobertura.")
        st.stop()

    # 4. Convertir Coordenadas
    coords = []
    for p in puntos:
        try:
            lat, lon, alt_pies = p[0], p[1], p[2]
            alt_m = 0 if alt_pies in [None, "ground"] else float(alt_pies) * 0.3048
            coords.append((float(lon), float(lat), alt_m))
        except:
            continue

    if not coords:
        st.error("❌ Error al procesar la integridad geométrica de los puntos.")
        st.stop()

    # 5. Generar y entregar archivo
    with st.spinner("Estructurando empaquetado KMZ..."):
        kmz_bytes = generar_kmz(coords, f"Ruta {matricula.upper()} - {fecha_str}")

    st.success("🎉 ¡Archivo KMZ generado con éxito!")
    
    st.download_button(
        label=f"📥 Descargar KMZ de {matricula.upper()}",
        data=kmz_bytes,
        file_name=f"traza_{matricula}_{fecha_str}.kmz",
        mime="application/vnd.google-earth.kmz"
    )
    st.balloons()
