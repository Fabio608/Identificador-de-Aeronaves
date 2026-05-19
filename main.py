import os
import re
import json
import requests
import simplekml
import streamlit as st

from datetime import datetime

# ============================================================
# CONFIG STREAMLIT
# ============================================================

st.set_page_config(
    page_title="FR24 → KMZ",
    page_icon="🛩️",
    layout="centered"
)

st.title("🛩️ Generador KMZ desde enlace FR24")

st.markdown("""
Pegá un enlace de Flightradar24 y el sistema intentará:

- detectar el vuelo
- buscar la traza
- generar un archivo KMZ
- permitir descarga
""")

st.warning("""
⚠️ IMPORTANTE

Flightradar24 no ofrece una API pública oficial gratuita para trazas históricas.
Este sistema intenta reconstruir rutas usando información pública y fuentes ADS-B abiertas.

Algunos vuelos pueden no estar disponibles.
""")

# ============================================================
# CONFIG
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

URL_ADSB = "https://api.adsb.one/v2"

# ============================================================
# FUNCIONES
# ============================================================

def extraer_datos_fr24(url):

    """
    Extrae matrícula y flight_id desde URL FR24
    """

    resultado = {
        "matricula": None,
        "flight_id": None
    }

    try:

        # ejemplo:
        # https://www.flightradar24.com/data/aircraft/tc-66#3fc194d1

        match = re.search(
            r"/aircraft/([^#]+)#([a-zA-Z0-9]+)",
            url
        )

        if match:

            resultado["matricula"] = (
                match.group(1)
                .strip()
                .lower()
            )

            resultado["flight_id"] = (
                match.group(2)
                .strip()
            )

    except:
        pass

    return resultado


def obtener_hex(matricula):

    """
    Traduce matrícula → HEX
    """

    try:

        url = f"{URL_ADSB}/registration/{matricula}"

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if r.status_code == 200:

            data = r.json()

            if (
                "ac" in data
                and len(data["ac"]) > 0
            ):

                return (
                    data["ac"][0]
                    .get("hex", "")
                    .lower()
                )

    except:
        pass

    return None


def obtener_traza(hex_code):

    """
    Busca posición LIVE aproximada
    """

    try:

        url = f"{URL_ADSB}/hex/{hex_code}"

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if r.status_code == 200:

            data = r.json()

            if (
                "ac" in data
                and len(data["ac"]) > 0
            ):

                ac = data["ac"][0]

                lat = ac.get("lat")
                lon = ac.get("lon")
                alt = ac.get("alt_baro", 0)

                if lat and lon:

                    return [{
                        "lat": lat,
                        "lon": lon,
                        "alt": alt
                    }]

    except:
        pass

    return []


def generar_kmz(coords, nombre):

    """
    Genera archivo KMZ
    """

    kml = simplekml.Kml()

    ruta = kml.newlinestring(
        name=nombre
    )

    ruta.coords = coords

    ruta.style.linestyle.color = (
        simplekml.Color.red
    )

    ruta.style.linestyle.width = 4

    ruta.altitudemode = (
        simplekml.AltitudeMode.absolute
    )

    ruta.extrude = 1

    archivo = "traza.kmz"

    kml.savekmz(archivo)

    with open(archivo, "rb") as f:
        data = f.read()

    os.remove(archivo)

    return data


# ============================================================
# INPUT
# ============================================================

url = st.text_input(
    "Pegá el link FR24:",
    placeholder="https://www.flightradar24.com/data/aircraft/tc-66#3fc194d1"
)

# ============================================================
# BOTÓN
# ============================================================

if st.button("🚀 Generar KMZ"):

    if not url:

        st.warning(
            "Pegá un enlace primero."
        )

        st.stop()

    # --------------------------------------------------------
    # EXTRAER DATOS URL
    # --------------------------------------------------------

    datos = extraer_datos_fr24(url)

    matricula = datos["matricula"]
    flight_id = datos["flight_id"]

    if not matricula:

        st.error(
            "No se pudo detectar matrícula."
        )

        st.stop()

    st.success(
        f"Matrícula detectada: "
        f"{matricula.upper()}"
    )

    st.info(
        f"Flight ID: {flight_id}"
    )

    # --------------------------------------------------------
    # OBTENER HEX
    # --------------------------------------------------------

    with st.spinner(
        "Buscando HEX ADS-B..."
    ):

        hex_code = obtener_hex(
            matricula.replace("-", "")
        )

    if not hex_code:

        st.error(
            "No se encontró HEX."
        )

        st.stop()

    st.success(
        f"HEX encontrado: "
        f"{hex_code.upper()}"
    )

    # --------------------------------------------------------
    # OBTENER TRAZA
    # --------------------------------------------------------

    with st.spinner(
        "Buscando posiciones..."
    ):

        puntos = obtener_traza(hex_code)

    if not puntos:

        st.error(
            "No se encontraron posiciones."
        )

        st.stop()

    # --------------------------------------------------------
    # COORDS
    # --------------------------------------------------------

    coords = []

    for p in puntos:

        try:

            lon = float(p["lon"])
            lat = float(p["lat"])

            alt = p.get("alt", 0)

            if alt in [None, "ground"]:
                alt = 0

            alt_m = float(alt) * 0.3048

            coords.append(
                (lon, lat, alt_m)
            )

        except:
            continue

    if len(coords) < 1:

        st.error(
            "Sin coordenadas válidas."
        )

        st.stop()

    # --------------------------------------------------------
    # SI SOLO HAY UN PUNTO
    # GENERAMOS MINI TRAZA
    # --------------------------------------------------------

    if len(coords) == 1:

        lon, lat, alt = coords[0]

        coords = [
            (lon, lat, alt),
            (lon + 0.01, lat + 0.01, alt)
        ]

    # --------------------------------------------------------
    # GENERAR KMZ
    # --------------------------------------------------------

    with st.spinner(
        "Generando KMZ..."
    ):

        kmz = generar_kmz(
            coords,
            f"Vuelo {matricula.upper()}"
        )

    st.success(
        "KMZ generado correctamente."
    )

    # --------------------------------------------------------
    # DESCARGA
    # --------------------------------------------------------

    fecha = datetime.utcnow().strftime(
        "%Y%m%d_%H%M"
    )

    st.download_button(
        label="📥 Descargar KMZ",
        data=kmz,
        file_name=(
            f"{matricula}_{fecha}.kmz"
        ),
        mime="application/vnd.google-earth.kmz"
    )

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    with st.expander("DEBUG"):

        st.write("Datos detectados:")
        st.json(datos)

        st.write("Coordenadas:")
        st.json(coords)
