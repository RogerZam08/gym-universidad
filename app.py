import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import time
import json
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Registro Gym U",
    page_icon="💪",
    layout="centered"
)

# --- ID DE TU HOJA DE CÁLCULO ---
ID_HOJA = "1X6m1hI3n0agp-uUru-dgaRIRU1AAv4E8Kf_0hYUkVdQ"

# --- CONEXIÓN CON GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = None
    
    if os.path.exists("credenciales.json"):
        with open("credenciales.json") as f:
            creds_dict = json.load(f)
    else:
        try:
            creds_dict = st.secrets["gcp_service_account"]
        except:
            pass

    if creds_dict is None:
        st.error("🚨 Error: No encuentro el archivo 'credenciales.json'.")
        st.stop()
    
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    
    client = gspread.authorize(credentials)
    
    try:
        sheet = client.open_by_key(ID_HOJA)
        return sheet
    except Exception as e:
        st.error(f"Error conectando con la hoja: {e}")
        st.stop()

# --- FUNCIONES DE AYUDA ---
def obtener_hora_ecuador():
    zona_ecuador = pytz.timezone('America/Guayaquil')
    ahora = datetime.now(zona_ecuador)
    return ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")

# --- INTERFAZ PRINCIPAL ---
def main():
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🏋️ Gym Universitario</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Sistema de Control de Acceso</p>", unsafe_allow_html=True)
    st.divider()

    # Conectar
    sh = conectar_google_sheets()
    
    try:
        ws_usuarios = sh.worksheet("Usuarios")
        ws_visitas = sh.worksheet("Visitas")
    except:
        st.error("⚠️ No encuentro las pestañas 'Usuarios' o 'Visitas'.")
        st.stop()

    # Variable de estado
    if 'formulario_activo' not in st.session_state:
        st.session_state.formulario_activo = False
    
    # Input de Cédula
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        cedula_input = st.text_input("Ingresa tu número de Cédula", 
                                     max_chars=10, 
                                     placeholder="Ej: 1712345678")
        boton_ingreso = st.button("Ingresar 🚀", use_container_width=True, type="primary")

    # --- LÓGICA PRINCIPAL ---
    if boton_ingreso:
        if not cedula_input:
            st.toast("⚠️ Por favor escribe un número.")
            return

        with st.spinner("🔄 Verificando..."):
            try:
                data = ws_usuarios.get_all_records()
                df = pd.DataFrame(data)
                
                usuario_encontrado = None
                
                if not df.empty:
                    df['Cedula'] = df['Cedula'].astype(str)
                    cedula_str = str(cedula_input).strip()
                    filtro = df[df['Cedula'] == cedula_str]
                    
                    if not filtro.empty:
                        usuario_encontrado = filtro.iloc[0]

                fecha, hora = obtener_hora_ecuador()

                # --- CASO 1: YA EXISTE (Copiar datos a Visitas) ---
                if usuario_encontrado is not None:
                    # CORRECCIÓN: Convertimos todo a string (str) explícitamente
                    # para eliminar el formato int64 que rompe el JSON
                    nombre = str(usuario_encontrado['Nombre'])
                    carrera = str(usuario_encontrado['Carrera'])
                    semestre = str(usuario_encontrado['Semestre']) 
                    correo = str(usuario_encontrado['Correo'])
                    sexo = str(usuario_encontrado['Sexo'])
                    
                    # Guardamos
                    ws_visitas.append_row([
                        fecha, 
                        hora, 
                        str(cedula_input),
                        nombre,
                        carrera,
                        semestre,
                        correo,
                        sexo
                    ])
                    
                    st.success(f"¡Bienvenido, **{nombre}**! ✅")
                    st.info(f"🕒 Registro guardado: {hora}")
                    time.sleep(3)
                    st.rerun()

                # --- CASO 2: NO EXISTE (Activar Formulario) ---
                else:
                    st.session_state.formulario_activo = True

            except Exception as e:
                st.error(f"Error del sistema: {e}")

    # --- MOSTRAR FORMULARIO SI ES NUEVO ---
    if st.session_state.formulario_activo:
        st.warning(f"La cédula **{cedula_input}** no está registrada.")
        st.markdown("### 📝 Registro de Nuevo Usuario")
        
        with st.form("form_nuevo"):
            col_a, col_b = st.columns(2)
            with col_a:
                nuevo_nombre = st.text_input("Nombre Completo")
                nuevo_carrera = st.text_input("Carrera")
                nuevo_sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
            with col_b:
                st.text_input("Cédula", value=cedula_input, disabled=True)
                nuevo_semestre = st.selectbox("Semestre", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Egresado"])
                nuevo_correo = st.text_input("Correo Institucional")
            
            guardar = st.form_submit_button("Guardar Registro")
            
            if guardar:
                if nuevo_nombre and nuevo_carrera and nuevo_correo:
                    try:
                        # Guardar en USUARIOS
                        ws_usuarios.append_row([
                            str(cedula_input), 
                            nuevo_nombre, 
                            nuevo_carrera, 
                            str(nuevo_semestre), 
                            nuevo_correo, 
                            nuevo_sexo
                        ])
                        
                        # Guardar en VISITAS
                        fecha, hora = obtener_hora_ecuador()
                        ws_visitas.append_row([
                            fecha, 
                            hora, 
                            str(cedula_input),
                            nuevo_nombre,
                            nuevo_carrera,
                            str(nuevo_semestre),
                            nuevo_correo, 
                            nuevo_sexo
                        ])
                        
                        st.balloons()
                        st.success("¡Registro Exitoso! Bienvenido al Gym.")
                        
                        time.sleep(3)
                        st.session_state.formulario_activo = False
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.error("Por favor completa todos los campos.")

    # --- FOOTER ---
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px;'>By: Roger Zambrano</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
