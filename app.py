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
    # 🎨 CABECERA PERSONALIZADA (Yachay Tech)
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
    if 'cedula_actual' not in st.session_state:
        st.session_state.cedula_actual = ""

    # --- INPUT DE CÉDULA ---
    # Si estamos editando, bloqueamos el input principal para que no cambien la cédula
    disabled_input = st.session_state.modo_edicion
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        cedula_input = st.text_input("Ingresa tu número de Cédula", 
                                     max_chars=10, 
                                     placeholder="Ej: 1712345678",
                                     disabled=disabled_input,
                                     value=st.session_state.cedula_actual if disabled_input else "")
        
        if not disabled_input:
            boton_ingreso = st.button("Ingresar 🚀", use_container_width=True, type="primary")
        else:
            boton_ingreso = False

    # --- LÓGICA DE INGRESO ---
    if boton_ingreso:
        st.session_state.cedula_actual = cedula_input # Guardamos la cédula
        
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

                # --- CASO 1: YA EXISTE ---
                if usuario_encontrado is not None:
                    nombre = str(usuario_encontrado['Nombre'])
                    
                    # Registrar Visita Automática
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
                    
                    # BOTÓN DE RECTIFICACIÓN
                    st.markdown("---")
                    st.markdown("¿Te equivocaste en tus datos o cambiaste de semestre?")
                    if st.button("🔄 Rectificar mis datos"):
                        st.session_state.modo_edicion = True
                        st.session_state.formulario_activo = True
                        st.rerun()
                    
                    # Limpieza automática si no edita
                    if not st.session_state.modo_edicion:
                        time.sleep(4)
                        st.rerun()

                # --- CASO 2: NO EXISTE ---
                else:
                    st.session_state.formulario_activo = True
                    st.session_state.modo_edicion = False # Es nuevo, no edición
                    st.rerun()

            except Exception as e:
                st.error(f"Error del sistema: {e}")

    # --- FORMULARIO (SIRVE PARA NUEVOS Y PARA EDICIÓN) ---
    if st.session_state.formulario_activo:
        
        titulo_form = "📝 Actualizar Datos" if st.session_state.modo_edicion else "📝 Registro Nuevo"
        st.markdown(f"### {titulo_form}")
        
        if st.session_state.modo_edicion:
            st.info("ℹ️ Al guardar, se sobrescribirán tus datos anteriores.")
        else:
            st.warning(f"La cédula **{st.session_state.cedula_actual}** no está registrada.")

        with st.form("form_datos"):
            col_a, col_b = st.columns(2)
            cedula_fija = st.session_state.cedula_actual
            
            with col_a:
                nuevo_nombre = st.text_input("Nombre Completo")
                nuevo_carrera = st.text_input("Carrera")
                nuevo_sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
            with col_b:
                st.text_input("Cédula", value=cedula_fija, disabled=True)
                nuevo_semestre = st.selectbox("Semestre", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Egresado"])
                nuevo_correo = st.text_input("Correo Institucional", placeholder="ejemplo@yachaytech.edu.ec")
            
            texto_boton = "Actualizar Datos" if st.session_state.modo_edicion else "Guardar Registro"
            guardar = st.form_submit_button(texto_boton)
            
            if guardar:
                # Validación básica
                if "@" not in nuevo_correo: # Puedes agregar 'yachaytech.edu.ec' si quieres ser estricto
                    st.error("⚠️ Correo inválido.")
                elif nuevo_nombre and nuevo_carrera:
                    try:
                        # --- LOGICA DE GUARDADO ---
                        fecha, hora = obtener_hora_ecuador()
                        
                        # Si es EDICIÓN: Buscamos la fila y sobrescribimos
                        if st.session_state.modo_edicion:
                            cell = ws_usuarios.find(str(cedula_fija))
                            num_fila = cell.row
                            # Actualizamos el rango de esa fila (Columnas A a F)
                            ws_usuarios.update(f"A{num_fila}:F{num_fila}", [[
                                str(cedula_fija), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                            ]])
                            st.success("¡Datos actualizados correctamente! 🔄")
                        
                        # Si es NUEVO: Agregamos al final
                        else:
                            ws_usuarios.append_row([
                                str(cedula_fija), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                            ])
                            # Solo registramos visita si es nuevo (si es edición, ya marcó entrada al buscarse)
                            ws_visitas.append_row([
                                fecha, hora, str(cedula_fija), nuevo_nombre, nuevo_carrera, str(nuevo_semestre), nuevo_correo, nuevo_sexo
                            ])
                            st.balloons()
                            st.success("¡Registro Exitoso!")

                        time.sleep(2)
                        # Reset total
                        st.session_state.formulario_activo = False
                        st.session_state.modo_edicion = False
                        st.session_state.cedula_actual = ""
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error guardando: {e}")
                else:
                    st.error("Faltan datos obligatorios.")
        
        # Botón para cancelar edición si se arrepienten
        if st.session_state.modo_edicion:
            if st.button("Cancelar"):
                st.session_state.formulario_activo = False
                st.session_state.modo_edicion = False
                st.session_state.cedula_actual = ""
                st.rerun()

    # --- FOOTER ---
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px;'>By: Roger Zambrano</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
