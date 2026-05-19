import streamlit as st
from datetime import datetime, timedelta

# ============================================================
# CONFIG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Monitor de Playback FR24",
    page_icon="🛰️",
    layout="centered"
)

st.title("🛰️ Monitor y Generador de Playback FR24")
st.markdown("""
Elegí una aeronave de tu listado de interés o ingresá una nueva, 
seleccioná la fecha y el sistema te generará los enlaces directos de auditoría.
""")

# ============================================================
# BASE DE DATOS LOCAL / LISTADO DE INTERÉS
# ============================================================
# Acá podés agregar, sacar o editar los aviones que te interesen monitorear siempre
AERONAVES_INTERES = {
    "TC-66 (Lockheed C-130H Hércules)": {"tipo": "aircraft", "identificador": "tc-66"},
    "TC-61 (Lockheed C-130H Hércules)": {"tipo": "aircraft", "identificador": "tc-61"},
    "LV-FQZ (Boeing 737 Aerolíneas)": {"tipo": "aircraft", "identificador": "lv-fqz"},
    "Misión FAG29 (Vuelo Bolivia)": {"tipo": "flight", "identificador": "fag29"},
    "Vuelo ARG1839 (Comodoro - Aeroparque)": {"tipo": "flight", "identificador": "arg1839"}
}

# ============================================================
# INTERFAZ DE USUARIO
# ============================================================
st.subheader("📌 1. Seleccionar Aeronave o Vuelo")

# Opción de elegir del listado o cargar uno manual
modo_seleccion = st.radio("Método de búsqueda:", ["Elegir de mi listado de favoritos", "Ingresar uno nuevo manualmente"])

if modo_seleccion == "Elegir de mi listado de favoritos":
    seleccionado = st.selectbox("Seleccioná el objetivo:", list(AERONAVES_INTERES.keys()))
    tipo_objetivo = AERONAVES_INTERES[seleccionado]["tipo"]
    id_objetivo = AERONAVES_INTERES[seleccionado]["identificador"]
else:
    tipo_objetivo = st.selectbox("Tipo de identificador:", ["aircraft (Por Matrícula)", "flight (Por Número de Vuelo)"]).split(" ")[0]
    id_objetivo = st.text_input("Ingresá el identificador (Ej: TC-66 o FAG29):", "").strip().lower().replace(" ", "")

st.subheader("📅 2. Configurar Fecha de Auditoría")
fecha_por_defecto = datetime.now() - timedelta(days=1)
fecha_seleccionada = st.date_input("Seleccioná el día del vuelo:", fecha_por_defecto)

# ============================================================
# CONSTRUCCIÓN DE ENLACES
# ============================================================
st.markdown("---")
st.subheader("🚀 3. Enlaces de Monitoreo Generados")

if id_objetivo:
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    
    if tipo_objetivo == "aircraft":
        # Link al historial completo de esa matrícula para buscar el código del playback (#3fc194d1, etc.)
        url_base = f"https://www.flightradar24.com/data/aircraft/{id_objetivo}"
        
        st.success(f"🎯 Objetivo: Matrícula **{id_objetivo.upper()}**")
        st.markdown(f"""
        Para ver el Playback de la matrícula **{id_objetivo.upper()}** del día **{fecha_str}**:
        1. Hacé clic en el botón de abajo para ir al historial oficial de la aeronave.
        2. Buscá la fila del día **{fecha_str}** en la tabla.
        3. Presioná el botón **'Play'** o **'Playback'** a la derecha de la fila dentro de Flightradar24.
        """)
        
        st.link_button(f"🌐 Abrir Historial de {id_objetivo.upper()} en FR24", url_base, type="primary")

    elif tipo_objetivo == "flight":
        # Link directo al historial de la ruta/vuelo
        url_base = f"https://www.flightradar24.com/data/flights/{id_objetivo}"
        
        st.success(f"🎯 Objetivo: Vuelo/Callsign **{id_objetivo.upper()}**")
        st.markdown(f"""
        Para auditar la ruta del vuelo **{id_objetivo.upper()}**:
        1. Abrí el enlace del historial de este número de vuelo.
        2. Buscá el tramo correspondiente al **{fecha_str}** y ejecutá el Playback con tu licencia para descargar el track definitivo.
        """)
        
        st.link_button(f"🌐 Abrir Historial del Vuelo {id_objetivo.upper()} en FR24", url_base, type="primary")
else:
    st.info("Configurá los campos de arriba para generar los accesos directos.")
