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
Buscá cualquier aeronave del mundo por su **Matrícula real** (Ej: LV-FQZ, TC-66, ZM421) 
o su código HEX. El sistema buscará su identidad y generará el archivo para Google Earth.
""")

URL_HISTORIAL_BASE = "https://adsb.fi/history"
URL_BUSCADOR_HEX = "https://api.adsb.one/v2/registration"  # API auxiliar para traducir matrículas en vivo

# =====================================================================
# FUNCIÓN DE TRADUCCIÓN AUTOMÁTICA (Matrícula -> HEX)
# =====================================================================
def obtener_hex_desde_matricula(matricula):
    """ Consulta una base de datos en vivo para transformar la matrícula a HEX """
    # Machetes manuales de emergencia por si la API externa falla con los militares
    machete = {
        "tc61": "e0224b", "tc64": "e0224d", "tc66": "e0224e", 
        "tc69": "e02250", "tc100": "e01862", "zm421": "43c5ef_r"
    }
    if matricula in machete:
        return machete[matricula]
        
    try:
        url = f"{URL_BUSCADOR_HEX}/{matricula}"
        respuesta = requests.get(url, timeout=6)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if "ac" in datos and len(datos["ac"]) > 0:
                return datos["ac"][0].get("hex", "").strip().lower()
    except:
        pass
    return None

# =====================================================================
# FLUJO CENTRAL DE TRABAJO
# =====================================================================
st.subheader("🔍 1. Configurar Búsqueda")

entrada_usuario = st.text_input("Ingresá la Matrícula (Ej: LV-FQZ, TC-66, ZM421):", 
                               placeholder="Ejemplo: LV-FQZ").strip().lower().replace(" ", "")

fecha_por_defecto = datetime.now() - timedelta(days=1)
fecha_seleccionada = st.date_input("Seleccioná la fecha del vuelo (en hora UTC):", fecha_por_defecto)

if st.button("🚀 Iniciar Análisis de Trayectoria", type="primary"):
    if not entrada_usuario:
        st.warning("⚠️ Por favor, ingresá un identificador primero.")
    else:
        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        st.subheader("📊 2. Resultado del Análisis")
        
        # Limpiamos el texto por si pusieron la palabra HEX por error
        if entrada_usuario.startswith("hex"):
            entrada_usuario = entrada_usuario.replace("hex", "")
        
        # Determinamos si el usuario ingresó un HEX directo o una matrícula
        # Un código HEX válido suele tener 6 caracteres y no llevar guiones
        es_hex_directo = len(entrada_usuario) == 6 and "-" not in entrada_usuario and not entrada_usuario.startswith("tc")
        
        if es_hex_directo:
            hex_code = entrada_usuario
            matricula_pantalla = f"HEX: {entrada_usuario.upper()}"
            st.info(f"Buscando directamente por código de transpondedor HEX...")
        else:
            # Quitamos el guion medio solo para la búsqueda interna si lo tuviera
            matricula_limpia = entrada_usuario.replace("-", "")
            st.info(f"🔍 Buscando código de transpondedor para la matrícula '{entrada_usuario.upper()}' en la base de datos mundial...")
            
            hex_code = obtener_hex_desde_matricula(matricula_limpia)
            matricula_pantalla = entrada_usuario.upper()

        if not hex_code:
            st.error(f"❌ No pudimos encontrar el código HEX indexado para la matrícula '{matricula_pantalla}'. Probá ingresando su código HEX de transpondedor de 6 caracteres directo si lo conocés.")
        else:
            st.info(f"🛰️ ¡Código encontrado! Identificador transpondedor: **[{hex_code.upper()}]**. Consultando trazas del día {fecha_str}...")

            # Consulta a la API de ADSB.fi histórica
            dos_primeros = hex_code[:2]
            url_peticion = f"{URL_HISTORIAL_BASE}/{fecha_str}/traces/{dos_primeros}/{hex_code}.json"

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                respuesta = requests.get(url_peticion, headers=headers, timeout=12)

                if respuesta.status_code == 200:
                    puntos = respuesta.json().get("trace", [])

                    if puntos and len(puntos) >= 5:
                        st.success(f"🚨 **¡Movimiento Detectado!** Se encontraron {len(puntos)} puntos de posición geográfica.")
                        
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
                            marcador.description = f"Objetivo: {matricula_pantalla}\nHEX: {hex_code.upper()}\nFecha: {fecha_str}"

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
                        st.warning(f"💤 La aeronave {matricula_pantalla} estuvo encendida pero no registró suficientes posiciones en vuelo.")
                
                elif respuesta.status_code == 404:
                    st.error(f"❌ **Sin novedades de vuelo:** El avión existe y su código es {hex_code.upper()}, pero no hay registros de movimiento para el día {fecha_str}. Recordá verificar si voló ese día exacto en hora UTC.")
                else:
                    st.error(f"⚠️ Error de respuesta del servidor (Código {respuesta.status_code}).")

            except requests.exceptions.Timeout:
                st.error("⏱️ Tiempo de espera agotado.")
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")
