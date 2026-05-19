import os
import json
import time
import simplekml
import streamlit as st

from playwright.sync_api import sync_playwright

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="FR24 → KMZ",
    page_icon="🛩️",
    layout="centered"
)

st.title("🛩️ Importador FR24 a KMZ")

st.markdown("""
Pegá un link de Flightradar24 y el sistema intentará:

- detectar el replay
- extraer la trayectoria
- generar un archivo KMZ
""")

# ============================================================
# INPUT
# ============================================================

url = st.text_input(
    "Pegá el link de Flightradar24:",
    placeholder="https://www.flightradar24.com/data/aircraft/tc-66#3fc194d1"
)

# ============================================================
# FUNCION PRINCIPAL
# ============================================================

def obtener_datos_vuelo(fr24_url):

    datos_encontrados = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        # ----------------------------------------------------
        # INTERCEPTAR RESPUESTAS
        # ----------------------------------------------------

        def interceptar(response):

            try:

                content_type = response.headers.get(
                    "content-type", ""
                )

                # buscamos respuestas JSON
                if "application/json" in content_type:

                    data = response.json()

                    # buscamos estructuras con lat/lon
                    texto = json.dumps(data)

                    if (
                        "lat" in texto.lower()
                        and "lon" in texto.lower()
                    ):

                        datos_encontrados.append(data)

            except:
                pass

        page.on("response", interceptar)

        # ----------------------------------------------------
        # ABRIR URL
        # ----------------------------------------------------

        page.goto(fr24_url, timeout=60000)

        # esperar carga
        page.wait_for_timeout(10000)

        browser.close()

    return datos_encontrados

# ============================================================
# EXTRAER COORDENADAS
# ============================================================

def buscar_coordenadas(objeto):

    coords = []

    def recorrer(x):

        if isinstance(x, dict):

            # detectar posibles puntos
            if (
                "lat" in x
                and "lon" in x
            ):

                try:

                    lat = float(x["lat"])
                    lon = float(x["lon"])

                    alt = 0

                    if "alt" in x:
                        alt = float(x["alt"])

                    coords.append(
                        (lon, lat, alt)
                    )

                except:
                    pass

            for v in x.values():
                recorrer(v)

        elif isinstance(x, list):

            for item in x:
                recorrer(item)

    recorrer(objeto)

    return coords

# ============================================================
# GENERAR KMZ
# ============================================================

def generar_kmz(coordenadas):

    kml = simplekml.Kml()

    ruta = kml.newlinestring(
        name="Vuelo FR24"
    )

    ruta.coords = coordenadas

    ruta.style.linestyle.width = 4
    ruta.style.linestyle.color = simplekml.Color.red

    ruta.altitudemode = simplekml.AltitudeMode.absolute

    ruta.extrude = 1

    nombre = "vuelo_fr24.kmz"

    kml.savekmz(nombre)

    with open(nombre, "rb") as f:
        data = f.read()

    os.remove(nombre)

    return data

# ============================================================
# BOTON
# ============================================================

if st.button("🚀 Importar vuelo"):

    if not url:

        st.warning("Pegá un link primero.")
        st.stop()

    with st.spinner("Abriendo FR24 y buscando trayectoria..."):

        datos = obtener_datos_vuelo(url)

    if not datos:

        st.error(
            "No se encontraron datos del replay."
        )

        st.stop()

    st.success(
        f"Se capturaron {len(datos)} respuestas JSON."
    )

    # --------------------------------------------------------
    # BUSCAR COORDENADAS
    # --------------------------------------------------------

    coordenadas_totales = []

    for bloque in datos:

        puntos = buscar_coordenadas(bloque)

        coordenadas_totales.extend(puntos)

    # eliminar duplicados
    coordenadas_totales = list(
        dict.fromkeys(coordenadas_totales)
    )

    st.info(
        f"Se encontraron "
        f"{len(coordenadas_totales)} puntos."
    )

    if len(coordenadas_totales) < 2:

        st.error(
            "No hubo suficientes coordenadas."
        )

        st.stop()

    # --------------------------------------------------------
    # GENERAR KMZ
    # --------------------------------------------------------

    with st.spinner("Generando KMZ..."):

        kmz_data = generar_kmz(
            coordenadas_totales
        )

    st.success("KMZ generado correctamente.")

    # --------------------------------------------------------
    # DESCARGA
    # --------------------------------------------------------

    st.download_button(
        label="📥 Descargar KMZ",
        data=kmz_data,
        file_name="vuelo_fr24.kmz",
        mime="application/vnd.google-earth.kmz"
    )

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    with st.expander("DEBUG"):

        st.write("Primeros puntos:")

        st.json(
            coordenadas_totales[:10]
        )
