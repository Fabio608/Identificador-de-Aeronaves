import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.title("Debug de la App")

# 1. Verificar si hay Secretos cargados
st.write("Verificando Secrets...")
if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
    st.success("✅ FIREBASE_SERVICE_ACCOUNT encontrado")
    try:
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        st.write("Configuración de credenciales cargada correctamente.")
        
        # 2. Inicializar Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            st.success("✅ Firebase inicializado")
    except Exception as e:
        st.error(f"❌ Error al inicializar Firebase: {e}")
else:
    st.error("❌ NO se encontró FIREBASE_SERVICE_ACCOUNT en los Secrets. Por favor, revísalos en Settings.")

st.write("Si ves los mensajes en verde, la app está funcionando. Si no, revisa el error arriba.")
