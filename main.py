import os
import requests
import simplekml
import streamlit as st
from datetime import datetime, timedelta

# =====================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT
# =====================================================================
st.set_page_config(page_title="Rastreador de Aeronaves", page_icon="🛩️", layout="centered")

st.title("🛩️ Rastreador y Generador de Trazas KMZ")
st.markdown("""
Buscá cualquier aeronave por su matrícula militar/civil o su código HEX, seleccioná la fecha 
y descargá su recorrido en formato tridimensional (.KMZ) para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"

# =====================================================================
# DICCIONARIO INTELIGENTE DE MATRÍCULAS (Traductor automático)
# =====================================================================
# El programa revisa esta lista primero. Si encuentra la matrícula, usa el HEX correcto de fondo.
DICCIONARIO_MATRICULAS = {
    # Fuerza Aérea Argentina (Hércules C-130)
    "tc61": "e0224b",
    "tc64": "e0224d",
    "tc66": "e0224e",
    "tc69": "e02250",
    "tc100": "e01862",
    
    # Aviación Militar Extranjera / Ejemplos
    "zm421": "43c5ef_r",  # Airbus A400M RAF (Usa extensión _r en esta red)
    "ae0133": "ae0133",   # C-17 Globemaster USAF
    "ae07ba": "ae07ba"    # C-17 Globemaster USAF (Alta cobertura)
}

# =====================================================================
# FLUJO CENTRAL DE TRABAJO
# =====================================================================
st.subheader("🔍 1. Configurar Búsqueda")

# Entrada única de texto sin límite de caracteres
entrada_usuario = st.text_input("Ingresá la Matrícula (Ej: TC66, ZM421) o Código HEX:", 
                               placeholder="Ejemplo: TC66 o E0224E").strip().lower().replace("-", "").replace(" ", "")

# Selector de fecha (Ayer por defecto)
fecha_por_defecto = datetime.now() - timedelta(days=1)
fecha_seleccionada = st.date_input("Seleccioná la fecha del vuelo (en hora UTC):", fecha_por_defecto)

if st.button("🚀 Iniciar Análisis de Trayectoria", type="primary"):
    if not entrada_usuario:
        st.warning("⚠️ Por favor, ingresá una matrícula o código primero.")
    else:
        # Evitamos que la palabra "hex" rompa la búsqueda si el usuario la escribe por error
        if entrada_usuario.startswith("hex"):
            entrada_usuario = entrada_usuario.replace("hex", "")

        # 1. Verificamos si lo que escribió el usuario está en nuestro diccionario inteligene
        if entrada_usuario in DICCIONARIO_MATRICULAS:
            hex_code = DICCIONARIO_MATRICULAS[entrada_usuario]
            matricula_pantalla = entrada_usuario.upper()
        else:
            # 2. Si no está, asumimos que puso el HEX directo (o una matrícula nueva)
            hex_code = entrada_usuario
            matricula_pantalla = entrada_usuario.upper()

        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        st.subheader("📊 2. Resultado del Análisis")
        st.info(f"Consultando registros del día **{fecha_str}** para **[{matricula_pantalla}]** usando el identificador **[{hex_code.upper()}]**...")

        if len(hex_code) < 2:
            st.error("❌ El identificador ingresado es demasiado corto.")
        else:
            # Construcción de la URL de consulta para la API de ADSB.fi
            dos_primeros = hex_code[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_str}/traces/{dos_primeros}/{hex_code}.json"

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                respuesta = requests.get(url_peticion, headers=headers, timeout=12)

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
                                # Conversión a metros para el despliegue correcto en Google Earth
                                alt_metros = 0 if alt_pies == "ground" or not alt_pies else int(alt_pies) * 0.3048
                                coordenadas.append((lon, lat, alt_metros))
                            except:
                                continue

                        if coordenadas:
                            # Dibujo de la trayectoria de vuelo
                            ruta = kml.newlinestring(name=f"Vuelo {matricula_pantalla} - {fecha_str}")
                            ruta.coords = coordenadas
                            ruta.extrude = 1  # Pared vertical tridimensional hacia el suelo
                            ruta.altitudemode = simplekml.AltitudeMode.absolute
                            ruta.style.linestyle.color = simplekml.Color.red  # Línea roja
                            ruta.style.linestyle.width = 4

                            # Marcador en el punto inicial del track
                            marcador = kml.newpoint(name="Inicio de Traza", coords=[coordenadas[0]])
                            marcador.description = f"Objetivo: {matricula_pantalla}\nIdentificador: {hex_code.upper()}\nFecha: {fecha_str}"

                            # Guardado temporal y empaquetado seguro en KMZ binario
                            nombre_temporal = f"temp_{hex_code}.kmz"
                            kml.savekmz(nombre_temporal)
                            with open(nombre_temporal, "rb") as f:
                                kmz_data = f.read()
                            os.remove(nombre_temporal)

                            # =====================================================
                            # 3. BOTÓN DE DESCARGA FINAL
                            # =====================================================
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
                        st.warning(f"💤 La aeronave {matricula_pantalla} estuvo encendida pero no registró suficientes posiciones en vuelo para armar una traza.")
                
                elif respuesta.status_code == 404:
                    st.error(f"❌ **Sin novedades:** No hay vuelos grabados para '{matricula_pantalla}' el día {fecha_str}. Recordá que si voló en zonas remotas (como el tramo de Bolivia del día 16), la red comunitaria abierta de ADSB.fi puede tener puntos ciegos por falta de antenas terrestres en esa región.")
                else:
                    st.error(f"⚠️ Error de respuesta del servidor externo (Código {respuesta.status_code}).")

            except requests.exceptions.Timeout:
                st.error("⏱️ Tiempo de espera agotado. El servidor de mapas tardó demasiado en responder.")
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")
