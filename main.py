import os
import requests
import simplekml
import streamlit as st
from datetime import datetime, timedelta

# =====================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT
# =====================================================================
st.set_page_config(page_title="Identificador de Aeronaves", page_icon="🛩️", layout="centered")

st.title("🛩️ Rastreador y Generador de Trazas KMZ")
st.markdown("""
Buscá cualquier aeronave por su identificador o matrícula, seleccioná la fecha y descargá 
su recorrido en formato tridimensional (.KMZ) para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# Diccionario interno de traducción rápida (podés seguir sumando las que quieras acá)
DICCIONARIO_MATRICULAS = {
    "zm421": "43c5ef",   # Airbus A400M RAF
    "t23": "34612a",     # Ejemplo militar
    "933dhc": "484bb8"   # Ejemplo DHC
}

# =====================================================================
# FLUJO CENTRAL DE TRABAJO (BUSCADOR SIN LÍMITES)
# =====================================================================
st.subheader("🔍 1. Configurar Búsqueda")

# Eliminamos la limitación de caracteres (max_chars) para que escribas lo que quieras
entrada_usuario = st.text_input("Ingresá la Matrícula o Código de la aeronave:", 
                               placeholder="Ej: ZM421, 944DHC, 43C5EF...").strip().lower().replace(" ", "")

# Selector de fecha (Ayer por defecto)
fecha_por_defecto = datetime.now() - timedelta(days=1)
fecha_seleccionada = st.date_input("Seleccioná la fecha del vuelo (en hora UTC):", fecha_por_defecto)

if st.button("🚀 Iniciar Análisis de Trayectoria", type="primary"):
    if not entrada_usuario:
        st.warning("⚠️ Por favor, ingresá una matrícula o código primero.")
    else:
        # 1. Intentamos traducir si existe en nuestro diccionario local
        if entrada_usuario in DICCIONARIO_MATRICULAS:
            hex_code = DICCIONARIO_MATRICULAS[entrada_usuario]
            matricula_pantalla = entrada_usuario.upper()
        else:
            # 2. Si no está, tomamos lo que escribió el usuario literalmente (sea el largo que sea)
            hex_code = entrada_usuario
            matricula_pantalla = entrada_usuario.upper()

        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        st.subheader("📊 2. Resultado del Análisis")
        st.info(f"Consultando registros del día **{fecha_str}** para el objetivo **[{matricula_pantalla}]**...")

        # Construcción dinámica de la URL usando la clave limpia
        # Si tiene menos de 2 caracteres por error, evitamos que rompa el script
        if len(hex_code) < 2:
            st.error("❌ El identificador ingresado es demasiado corto para ser procesado.")
        else:
            dos_primeros = hex_code[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_str}/traces/{dos_primeros}/{hex_code}.json"

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                respuesta = requests.get(url_peticion, headers=headers, timeout=12)

                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])

                    if puntos and len(puntos) >= 5:
                        st.success(f"🚨 **¡Movimiento Detectado!** Se encontraron {len(puntos)} puntos de posición.")
                        
                        # GENERACIÓN DEL ARCHIVO .KMZ
                        kml = simplekml.Kml()
                        coordenadas = []

                        for p in puntos:
                            try:
                                lat, lon, alt_pies = p[0], p[1], p[2]
                                alt_metros = 0 if alt_pies == "ground" or not alt_pies else int(alt_pies) * 0.3048
                                coordenadas.append((lon, lat, alt_metros))
                            except:
                                continue

                        if coordenadas:
                            ruta = kml.newlinestring(name=f"Vuelo {matricula_pantalla} - {fecha_str}")
                            ruta.coords = coordenadas
                            ruta.extrude = 1  
                            ruta.altitudemode = simplekml.AltitudeMode.absolute
                            ruta.style.linestyle.color = simplekml.Color.red  
                            ruta.style.linestyle.width = 4

                            marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                            marcador.description = f"Objetivo: {matricula_pantalla}\nIdentificador: {hex_code.upper()}\nFecha: {fecha_str}"

                            nombre_temporal = f"temp_{hex_code}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)

                            st.markdown("---")
                            st.subheader("💾 3. Guardar Trayectoria")
                            st.download_button(
                                label=f"📥 Descargar archivo .KMZ de {matricula_pantalla}",
                                data=kmz_data,
                                file_name=f"traza_{matricula_pantalla}_{fecha_str}.kmz",
                                mime="application/vnd.google-earth.kmz"
                            )
                            st.balloons()
                    else:
                        st.warning(f"💤 La aeronave {matricula_pantalla} fue detectada en tierra o sin suficientes puntos de movimiento.")
                
                elif respuesta.status_code == 404:
                    st.error(f"❌ **Sin novedades:** No hay registros para '{matricula_pantalla}' en la fecha {fecha_str} bajo el identificador '{hex_code}'. Verificá si el código de rastreo en ADSB.fi es correcto o probá con el día anterior/posterior.")
                else:
                    st.error(f"⚠️ Error de respuesta del servidor (Código {respuesta.status_code}).")

            except requests.exceptions.Timeout:
                st.error("⏱️ Tiempo de espera agotado. El servidor tardó demasiado en responder.")
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")
