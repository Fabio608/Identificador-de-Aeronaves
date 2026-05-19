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
Buscá cualquier aeronave por su identificador para analizar su actividad del día de ayer 
en la red **ADSB.fi** y descargar su recorrido en formato tridimensional para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# Diccionario interno de traducción rápida para comodidad del usuario
DICCIONARIO_MATRICULAS = {
    "zm421": "43c5ef",   # Airbus A400M RAF
    "t23": "34612a",     # Ejemplo militar
    "933dhc": "484bb8"   # Ejemplo DHC
}

# =====================================================================
# FLUJO CENTRAL DE TRABAJO (BUSCADOR PRINCIPAL)
# =====================================================================
st.subheader("🔍 1. Buscar Aeronave")

# Un único casillero grande en el centro de la pantalla
entrada_usuario = st.text_input("Ingresá la Matrícula o Código HEX de la aeronave:", 
                               placeholder="Ej: ZM421 o 43C5EF").strip().lower().replace(" ", "")

if st.button("🚀 Iniciar Análisis del Día Anterior", type="primary"):
    if not entrada_usuario:
        st.warning("⚠️ Por favor, ingresá una matrícula o código válido primero.")
    else:
        # Verificamos si el usuario escribió una matrícula conocida para traducirla a HEX
        if entrada_usuario in DICCIONARIO_MATRICULAS:
            hex_code = DICCIONARIO_MATRICULAS[entrada_usuario]
            matricula_pantalla = entrada_usuario.upper()
        else:
            # Si no está en el diccionario, asumimos que el usuario puso el HEX directo
            hex_code = entrada_usuario
            matricula_pantalla = entrada_usuario.upper()

        # Validación básica de longitud del código hexadecimal para la API
        if len(hex_code) != 6:
            st.error("❌ El identificador debe tener 6 caracteres (Ej: 43C5EF). Si ingresaste una matrícula nueva, probá cargando directamente su código HEX de transpondedor.")
        else:
            fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            st.subheader("📊 2. Resultado del Análisis")
            st.info(f"Consultando registros históricos del día **{fecha_ayer}** para el objetivo **[{matricula_pantalla}]**...")

            # Construcción de la URL de la API de ADSB.fi
            dos_primeros = hex_code[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_ayer}/traces/{dos_primeros}/{hex_code}.json"

            try:
                respuesta = requests.get(url_peticion, timeout=12)

                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])

                    if puntos and len(puntos) >= 5:
                        st.success(f"🚨 **¡Movimiento Detectado!** Se encontraron {len(puntos)} puntos de posición geográfica.")
                        
                        # =====================================================
                        # GENERACIÓN DEL ARCHIVO GEOGRÁFICO .KMZ
                        # =====================================================
                        kml = simplekml.Kml()
                        coordenadas = []

                        for p in puntos:
                            try:
                                lat, lon, alt_pies = p[0], p[1], p[2]
                                # Conversión de pies a metros para el dibujo en Google Earth
                                alt_metros = 0 if alt_pies == "ground" or not alt_pies else int(alt_pies) * 0.3048
                                coordenadas.append((lon, lat, alt_metros))
                            except:
                                continue

                        if coordenadas:
                            # Dibujo de la línea de la trayectoria
                            ruta = kml.newlinestring(name=f"Vuelo {matricula_pantalla} - {fecha_ayer}")
                            ruta.coords = coordenadas
                            ruta.extrude = 1  # Crea el efecto de pared tridimensional hacia el suelo
                            ruta.altitudemode = simplekml.AltitudeMode.absolute
                            ruta.style.linestyle.color = simplekml.Color.red  # Línea roja de seguimiento
                            ruta.style.linestyle.width = 4

                            # Marcador en el punto de inicio
                            marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                            marcador.description = f"Objetivo: {matricula_pantalla}\nHEX: {hex_code.upper()}\nFecha: {fecha_ayer}"

                            # Empaquetado seguro en formato KMZ binario
                            nombre_temporal = f"temp_{hex_code}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)

                            # =====================================================
                            # PASO 3: BOTÓN DE DESCARGA FINAL
                            # =====================================================
                            st.markdown("---")
                            st.subheader("💾 3. Guardar Trayectoria")
                            st.download_button(
                                label=f"📥 Descargar archivo .KMZ de {matricula_pantalla}",
                                data=kmz_data,
                                file_name=f"traza_{matricula_pantalla}_{fecha_ayer}.kmz",
                                mime="application/vnd.google-earth.kmz"
                            )
                            st.balloons()
                    else:
                        st.warning(f"💤 **Sin registros suficientes:** La aeronave {matricula_pantalla} estuvo encendida pero no generó una traza de vuelo válida ayer.")
                
                elif respuesta.status_code == 404:
                    st.error(f"❌ **Sin novedades:** La aeronave {matricula_pantalla} no registró ningún tipo de movimiento o emisión ayer en la red de antenas.")
                else:
                    st.error(f"⚠️ Error de conexión con el servidor (Código {respuesta.status_code}). Proba de nuevo en unos minutos.")

            except requests.exceptions.Timeout:
                st.error("⏱️ Tiempo de espera agotado. El servidor de datos está saturado, intentá nuevamente.")
            except Exception as e:
                st.error(f"❌ Ocurrió un error inesperado durante el procesamiento: {e}")
