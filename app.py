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
    page_title="Registro Gym Yachay",
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
        st.error("🚨 Error: No encuentro credenciales.")
        st.stop()
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
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
    # 🎨 CABECERA YACHAY TECH
    st.markdown("<h1 style='text-align: center; color: #005eb8;'>Registro Gym</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-weight: bold;'>YACHAY TECH</h2>", unsafe_allow_html=True)
    st.divider()

    # Conectar
    sh = conectar_google_sheets()
    try:
        ws_usuarios = sh.worksheet("Usuarios")
        ws_visitas = sh.worksheet("Visitas")
    except:
        st.error("⚠️ No encuentro las pestañas 'Usuarios' o 'Visitas'.")
        st.stop()

    # --- VARIABLES DE ESTADO ---
    if 'formulario_activo' not in st.session_state:
        st.session_state.formulario_activo = False
    if 'modo_edicion' not in st.session_state:
        st.session_state.modo_edicion = False
    if 'cedula_previa' not in st.session_state:
        st.session_state.cedula_previa = ""

    # --- PANTALLA PRINCIPAL (SI NO HAY FORMULARIO ACTIVO) ---
    if not st.session_state.formulario_activo:
        
        # 1. Input de Cédula
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            cedula_input = st.text_input("Ingresa tu número de Cédula", 
                                         max_chars=10, 
                                         placeholder="Ej: 1712345678")
            boton_ingreso = st.button("Ingresar 🚀", use_container_width=True, type="primary")

        # 2. Lógica de Ingreso (Check-in)
        if boton_ingreso:
            if not cedula_input:
                st.toast("⚠️ Por favor escribe un número.")
            else:
                st.session_state.cedula_previa = cedula_input # Guardamos para el form
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

                        # --- CASO: YA EXISTE (ENTRADA EXITOSA) ---
                        if usuario_encontrado is not None:
                            nombre = str(usuario_encontrado['Nombre'])
                            ws_visitas.append_row([
                                fecha, hora, str(cedula_input),
                                nombre,
                                str(usuario_encontrado['Carrera']),
                                str(usuario_encontrado['Semestre']),
                                str(usuario_encontrado['Correo']),
                                str(usuario_encontrado['Sexo'])
                            ])
                            st.success(f"¡Bienvenido, **{nombre}**! ✅")
                            st.info(f"🕒 Hora: {hora}")
                            time.sleep(3)
                            st.rerun()

                        # --- CASO: NO EXISTE (MANDAR A REGISTRO) ---
                        else:
                            st.session_state.formulario_activo = True
                            st.session_state.modo_edicion = False # Es nuevo
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

        # 3. OPCIÓN DE RECTIFICAR (SIEMPRE VISIBLE ABAJO)
        st.markdown("<br><br>", unsafe_allow_html=True) # Espacio
        with st.expander("🛠️ ¿Necesitas corregir tus datos?", expanded=False):
            st.caption("Usa esta opción si cambiaste de semestre, carrera o escribiste mal tu nombre.")
            if st.button("Ir al formulario de actualización"):
                st.session_state.modo_edicion = True
                st.session_state.formulario_activo = True
                # Si escribió algo en el input principal, lo usamos
                if cedula_input:
                    st.session_state.cedula_previa = cedula_input
                st.rerun()

    # --- PANTALLA DE FORMULARIO (NUEVO O EDICIÓN) ---
    else:
        titulo = "📝 Actualizar Datos" if st.session_state.modo_edicion else "📝 Registro Nuevo"
        st.markdown(f"### {titulo}")
        
        if st.session_state.modo_edicion:
            st.info("ℹ️ Al guardar, se sobrescribirá tu información en la base de datos.")

        with st.form("form_datos"):
            # Si venimos de rectificar sin haber puesto cédula, permitimos escribirla
            cedula_default = st.session_state.cedula_previa
            disabled_cedula = True if (st.session_state.cedula_previa and not st.session_state.modo_edicion) else False
            
            # Si está en modo edición y no hay cédula, debe poder escribirla
            if st.session_state.modo_edicion and not cedula_default:
                disabled_cedula = False

            col_a, col_b = st.columns(2)
            with col_a:
                val_cedula = st.text_input("Cédula", value=cedula_default, disabled=disabled_cedula)
                nuevo_nombre = st.text_input("Nombre Completo")
                nuevo_sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
            with col_b:
                nuevo_carrera = st.text_input("Carrera")
                nuevo_semestre = st.selectbox("Semestre", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Egresado"])
                nuevo_correo = st.text_input("Correo Institucional", placeholder="usuario@yachaytech.edu.ec")
            
            texto_btn = "Actualizar" if st.session_state.modo_edicion else "Registrarme"
            guardar = st.form_submit_button(texto_btn)
            
            # Botón cancelar (fuera del form visualmente o lógica de escape)
            
        if st.button("Cancelar / Volver"):
            st.session_state.formulario_activo = False
            st.session_state.modo_edicion = False
            st.rerun()

        if guardar:
            # Usamos el valor del input, sea que estuviera deshabilitado o no
            cedula_final = val_cedula
            
            if "@" not in nuevo_correo:
                st.error("⚠️ Correo inválido.")
            elif not cedula_final:
                st.error("⚠️ Falta la cédula.")
            elif nuevo_nombre and nuevo_carrera:
                try:
                    fecha, hora = obtener_hora_ecuador()
                    
                    # --- LÓGICA DE ACTUALIZACIÓN ---
                    if st.session_state.modo_edicion:
                        # Buscar si existe para sobrescribir
                        try:
                            cell = ws_usuarios.find(str(cedula_final))
                            fila = cell.row
                            ws_usuarios.update(f"A{fila}:F{fila}", [[
                                str(cedula_final), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                            ]])
                            st.success("✅ ¡Datos actualizados correctamente!")
                        except gspread.exceptions.CellNotFound:
                            # Si intentó editar pero no existía, lo creamos como nuevo
                            ws_usuarios.append_row([
                                str(cedula_final), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                            ])
                            st.success("✅ Usuario no existía, se ha creado uno nuevo.")

                    # --- LÓGICA DE NUEVO REGISTRO ---
                    else:
                        ws_usuarios.append_row([
                            str(cedula_final), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                        ])
                        # Registrar visita también
                        ws_visitas.append_row([
                            fecha, hora, str(cedula_final), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                        ])
                        st.balloons()
                        st.success("✅ ¡Registro completado!")

                    time.sleep(2)
                    st.session_state.formulario_activo = False
                    st.session_state.modo_edicion = False
                    st.session_state.cedula_previa = ""
                    st.rerun()

                except Exception as e:
                    st.error(f"Error guardando: {e}")
            else:
                st.error("Faltan datos obligatorios.")

    # --- FOOTER ---
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: black ; font-size: 13px;'>By: Roger Zambrano</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
