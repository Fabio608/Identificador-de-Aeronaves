import os
import re
import requests
import simplekml
import streamlit as st

from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =====================================================================
# CONFIGURACIÓN GENERAL
# =====================================================================

st.set_page_config(
    page_title="Rastreador de Aeronaves",
    page_icon="🛩️",
    layout="centered"
)

st.title("🛩️ Rastreador y Generador de Trazas KMZ")

st.markdown("""
Buscá aeronaves por:

- Matrícula real (LV-FQZ, TC-66, ZM421)
- Código HEX ADS-B

El sistema buscará su historial y generará un archivo compatible con Google Earth.
""")

st.info("""
ℹ️ Importante:
ADSB.fi no registra TODOS los vuelos del mundo.
La disponibilidad depende de:
- cobertura ADS-B
- receptores cercanos
- MLAT
- zonas militares
- transponder activo
""")

# =====================================================================
# URLs BASE
# =====================================================================

URL_HISTORIAL_BASE = "https://adsb.fi/history"
URL_BUSCADOR_HEX = "https://api.adsb.one/v2/registration"

# =====================================================================
# SESIÓN HTTP ROBUSTA
# =====================================================================

session = requests.Session()

retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)

session.mount("https://", HTTPAdapter(max_retries=retries))

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================

def es_hex_valido(valor):
    """
    Verifica si el valor parece un HEX ADS-B válido
    """
    return bool(re.fullmatch(r"[0-9a-fA-F]{6,8}(_r)?", valor))


def obtener_hex_desde_matricula(matricula):
    """
    Traduce matrícula -> HEX usando API externa
    """

    # Mapeo manual para aeronaves especiales/militares
    machete = {
        "tc61": "e0224b",
        "tc64": "e0224d",
        "tc66": "e0224e",
        "tc69": "e02250",
        "tc100": "e01862",
        "zm421": "43c5ef_r"
    }

    if matricula in machete:
        return machete[matricula]

    try:
        url = f"{URL_BUSCADOR_HEX}/{matricula}"

        respuesta = session.get(
            url,
            headers=HEADERS,
            timeout=8
        )

        if respuesta.status_code == 200:

            datos = respuesta.json()

            if "ac" in datos and len(datos["ac"]) > 0:

                hex_code = datos["ac"][0].get("hex")

                if hex_code:
                    return hex_code.strip().lower()

    except Exception as e:
        st.warning(f"Error consultando API de matrículas: {e}")

    return None


def convertir_altitud(alt_pies):
    """
    Convierte pies -> metros de forma segura
    """

    try:

        if alt_pies in ["ground", None, "", "null"]:
            return 0

        return float(alt_pies) * 0.3048

    except:
        return 0


def extraer_coordenadas(trace):
    """
    Procesa el trace ADS-B y devuelve coordenadas KML
    """

    coordenadas = []

    for punto in trace:

        try:
            # Formato habitual:
            # [timestamp, lat, lon, alt, ...]
            lat = punto[1]
            lon = punto[2]

            alt_pies = punto[3] if len(punto) > 3 else 0

            alt_metros = convertir_altitud(alt_pies)

            coordenadas.append(
                (lon, lat, alt_metros)
            )

        except Exception:
            continue

    return coordenadas


def generar_kmz(coordenadas, nombre, fecha, hex_code):
    """
    Genera KMZ temporal y devuelve bytes
    """

    kml = simplekml.Kml()

    ruta = kml.newlinestring(
        name=f"Vuelo {nombre} - {fecha}"
    )

    ruta.coords = coordenadas
    ruta.extrude = 1
    ruta.altitudemode = simplekml.AltitudeMode.absolute

    # Estilo visual
    ruta.style.linestyle.color = simplekml.Color.red
    ruta.style.linestyle.width = 4

    # Punto inicial
    inicio = kml.newpoint(
        name="Inicio de Traza",
        coords=[coordenadas[0]]
    )

    inicio.description = f"""
    Aeronave: {nombre}
    HEX: {hex_code.upper()}
    Fecha UTC: {fecha}
    """

    # Punto final
    final = kml.newpoint(
        name="Fin de Traza",
        coords=[coordenadas[-1]]
    )

    final.style.iconstyle.color = simplekml.Color.yellow

    nombre_temp = f"temp_{hex_code}.kmz"

    kml.savekmz(nombre_temp)

    with open(nombre_temp, "rb") as f:
        kmz_data = f.read()

    os.remove(nombre_temp)

    return kmz_data


# =====================================================================
# INTERFAZ
# =====================================================================

st.subheader("🔍 Configurar búsqueda")

entrada_original = st.text_input(
    "Ingresá Matrícula o HEX:",
    placeholder="Ej: LV-FQZ"
)

fecha_default = datetime.utcnow() - timedelta(days=1)

fecha_seleccionada = st.date_input(
    "Seleccioná fecha UTC:",
    fecha_default
)

modo_debug = st.checkbox("Mostrar debug técnico")

# =====================================================================
# BOTÓN PRINCIPAL
# =====================================================================

if st.button("🚀 Iniciar análisis", type="primary"):

    entrada_usuario = (
        entrada_original
        .strip()
        .lower()
        .replace(" ", "")
    )

    if not entrada_usuario:

        st.warning("⚠️ Ingresá una matrícula o código HEX.")

        st.stop()

    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")

    # ---------------------------------------------------------------
    # LIMPIEZA DE ENTRADA
    # ---------------------------------------------------------------

    if entrada_usuario.startswith("hex"):
        entrada_limpia = entrada_usuario.replace("hex", "")
    else:
        entrada_limpia = entrada_usuario

    # ---------------------------------------------------------------
    # DETECCIÓN HEX / MATRÍCULA
    # ---------------------------------------------------------------

    if es_hex_valido(entrada_limpia):

        hex_code = entrada_limpia.lower()

        matricula_pantalla = f"HEX {hex_code.upper()}"

        st.info("🛰️ Búsqueda directa por código HEX.")

    else:

        matricula_limpia = entrada_limpia.replace("-", "")

        st.info(
            f"🔍 Buscando HEX asociado a matrícula "
            f"{entrada_usuario.upper()}..."
        )

        hex_code = obtener_hex_desde_matricula(
            matricula_limpia
        )

        matricula_pantalla = entrada_usuario.upper()

    # ---------------------------------------------------------------
    # VALIDACIÓN HEX
    # ---------------------------------------------------------------

    if not hex_code:

        st.error(
            f"No pudimos encontrar el código HEX "
            f"para '{matricula_pantalla}'."
        )

        st.stop()

    st.success(
        f"HEX encontrado: {hex_code.upper()}"
    )

    # ---------------------------------------------------------------
    # CONSULTA HISTORIAL
    # ---------------------------------------------------------------

    dos_primeros = hex_code[:2]

    url_peticion = (
        f"{URL_HISTORIAL_BASE}/"
        f"{fecha_str}/traces/"
        f"{dos_primeros}/"
        f"{hex_code}.json"
    )

    st.info("📡 Consultando historial ADS-B...")

    try:

        respuesta = session.get(
            url_peticion,
            headers=HEADERS,
            timeout=15
        )

        # ============================================================
        # RESPUESTA OK
        # ============================================================

        if respuesta.status_code == 200:

            datos = respuesta.json()

            trace = datos.get("trace", [])

            if modo_debug:

                st.subheader("DEBUG")

                st.write("URL consultada:")
                st.code(url_peticion)

                st.write("Primeros puntos recibidos:")

                if len(trace) > 0:
                    st.json(trace[:5])
                else:
                    st.warning("Sin datos trace.")

            # -------------------------------------------------------
            # VALIDAR TRACE
            # -------------------------------------------------------

            if not trace or len(trace) < 5:

                st.warning(
                    "La aeronave no registró suficientes "
                    "posiciones para generar una traza."
                )

                st.stop()

            # -------------------------------------------------------
            # EXTRAER COORDENADAS
            # -------------------------------------------------------

            coordenadas = extraer_coordenadas(trace)

            if len(coordenadas) < 2:

                st.error(
                    "No se pudieron procesar coordenadas válidas."
                )

                st.stop()

            # -------------------------------------------------------
            # ESTADÍSTICAS
            # -------------------------------------------------------

            st.success(
                f"✅ Se detectaron "
                f"{len(coordenadas)} puntos de vuelo."
            )

            st.markdown("---")

            st.subheader("📈 Resumen")

            st.metric("Puntos GPS", len(coordenadas))

            altitudes = [c[2] for c in coordenadas]

            alt_max = max(altitudes)

            st.metric(
                "Altitud máxima",
                f"{int(alt_max)} m"
            )

            # -------------------------------------------------------
            # GENERAR KMZ
            # -------------------------------------------------------

            with st.spinner("Generando archivo KMZ..."):

                kmz_data = generar_kmz(
                    coordenadas,
                    matricula_pantalla,
                    fecha_str,
                    hex_code
                )

            st.success("KMZ generado correctamente.")

            # -------------------------------------------------------
            # DESCARGA
            # -------------------------------------------------------

            st.markdown("---")

            st.subheader("💾 Descargar")

            st.download_button(
                label="📥 Descargar archivo KMZ",
                data=kmz_data,
                file_name=(
                    f"traza_"
                    f"{matricula_pantalla}_"
                    f"{fecha_str}.kmz"
                ),
                mime="application/vnd.google-earth.kmz"
            )

            st.balloons()

        # ============================================================
        # 404
        # ============================================================

        elif respuesta.status_code == 404:

            st.error(
                f"No hay registros de vuelo para "
                f"{matricula_pantalla} "
                f"en la fecha {fecha_str} UTC."
            )

        # ============================================================
        # OTROS ERRORES
        # ============================================================

        else:

            st.error(
                f"Error del servidor ADS-B "
                f"(HTTP {respuesta.status_code})"
            )

    except requests.exceptions.Timeout:

        st.error(
            "⏱️ Tiempo de espera agotado."
        )

    except requests.exceptions.ConnectionError:

        st.error(
            "🌐 Error de conexión con ADSB.fi"
        )

    except Exception as e:

        st.error(
            f"❌ Error inesperado:\n{e}"
        )
