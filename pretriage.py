import streamlit as st
import pandas as pd
import mysql.connector
import hashlib
from datetime import datetime
from streamlit_autorefresh import st_autorefresh  # 👈 asegúrate de instalarlo: pip install streamlit-autorefresh

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema Médico", page_icon="🏥", layout="wide")
st.title("🏥 Sistema Médico Hospitalario")

# --- CONEXIÓN CON RAILWAY ---
def conectar():
    try:
        conn = mysql.connector.connect(
            host="nozomi.proxy.rlwy.net",
            port=39267,
            user="root",
            password="RIcZDpRThXVrkfwKgACLDbakSLIKcfmG",
            database="railway"
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"❌ Error al conectar con la base de datos: {err}")
        return None

# --- CIFRADO DE CONTRASEÑAS ---
def hash_contrasena(contrasena):
    return hashlib.sha256(contrasena.encode()).hexdigest()

# --- LOGIN ---
def login(usuario, contrasena):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE usuario = %s", (usuario,))
    user = cursor.fetchone()
    conn.close()
    if user and user["password"] == hash_contrasena(contrasena):
        return user
    return None

# --- REGISTRAR USUARIO (SIN REPETIDOS) ---
def registrar_usuario(usuario, contrasena, rol):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE usuario = %s", (usuario,))
        existente = cursor.fetchone()
        if existente:
            return {"status": "error", "mensaje": "⚠️ El nombre de usuario ya está registrado."}

        cursor.execute(
            "INSERT INTO users (usuario, password, role) VALUES (%s, %s, %s)",
            (usuario, hash_contrasena(contrasena), rol)
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "mensaje": "✅ Usuario creado correctamente."}
    except Exception as e:
        return {"status": "error", "mensaje": f"❌ Error al registrar usuario: {e}"}

# --- SESIÓN ---
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None

# ================================================================
# 🔐 LOGIN / REGISTRO
# ================================================================
if not st.session_state.usuario:
    menu_inicio = st.sidebar.selectbox("Menú", ["Iniciar sesión", "Crear cuenta nueva"])

    if menu_inicio == "Iniciar sesión":
        st.subheader("🔐 Inicio de Sesión")
        usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            user = login(usuario, contrasena)
            if user:
                st.session_state.usuario = user["usuario"]
                st.session_state.rol = user["role"]
                st.success(f"Bienvenido {user['usuario']} 👋 — Rol: {user['role']}")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

    elif menu_inicio == "Crear cuenta nueva":
        st.subheader("🆕 Crear una cuenta")
        nuevo_usuario = st.text_input("Nombre de usuario")
        nueva_contrasena = st.text_input("Contraseña", type="password")
        rol = st.selectbox("Rol", ["Enfermero", "Doctor"])
        if st.button("Registrar"):
            resultado = registrar_usuario(nuevo_usuario, nueva_contrasena, rol)
            if resultado["status"] == "ok":
                st.success(resultado["mensaje"])
            else:
                st.warning(resultado["mensaje"])

# ================================================================
# 🧑‍⚕️ PANEL PRINCIPAL
# ================================================================
else:
    st.sidebar.write(f"👋 Bienvenido, **{st.session_state.usuario}** ({st.session_state.rol})")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

    # ================================================================
    # 🧑‍⚕️ PANEL DE ENFERMERO
    # ================================================================
    if st.session_state.rol == "Enfermero":
        st.header("🧑‍⚕️ Registro de Pacientes (Enfermería)")
        with st.form("formulario_enfermero"):
            nombre = st.text_input("👤 Nombre completo")
            edad = st.number_input("🎂 Edad", min_value=0, max_value=120, step=1)
            sexo = st.selectbox("⚧ Sexo", ["Masculino", "Femenino"])
            peso = st.number_input("⚖️ Peso (kg)", min_value=0.0, step=0.1)
            altura = st.number_input("📏 Altura (cm)", min_value=0.0, step=0.1)
            pulso = st.number_input("❤️ Pulso (bpm)", min_value=0)
            spo2 = st.number_input("🫁 SpO₂ (%)", min_value=0, max_value=100, step=1)
            temperatura = st.number_input("🌡️ Temperatura (°C)", min_value=0.0, step=0.1)
            presion = st.text_input("🩸 Presión arterial (ej: 120/80)")
            enfermedades = st.text_area("🧬 Enfermedades Crónicas")
            alergias = st.text_area("🤧 Alergias")
            cirugias = st.text_area("🩹 Cirugías previas")
            medicacion = st.text_area("💊 Medicación permanente")
            observaciones = st.text_area("📝 Observaciones del enfermero")

            enviado = st.form_submit_button("💾 Guardar registro")

        if enviado:
            if nombre:
                try:
                    conn = conectar()
                    cursor = conn.cursor()
                    sql = """
                    INSERT INTO pre_triage (
                        FechaHora, Nombre, Edad, Sexo, Peso, Altura, Pulso, SpO2,
                        Temperatura, Presion, EnfermedadesCronicas, Alergias,
                        Cirugias, MedicacionPermanente, Observaciones, Estado
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """
                    valores = (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        nombre, edad, sexo, peso, altura, pulso, spo2,
                        temperatura, presion, enfermedades, alergias,
                        cirugias, medicacion, observaciones, "Pendiente"  # 👈 Estado por defecto
                    )
                    cursor.execute(sql, valores)
                    conn.commit()
                    conn.close()
                    st.success("✅ Registro guardado correctamente. Estado: Pendiente.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")
            else:
                st.error("⚠️ Debes ingresar al menos el nombre del paciente.")

    # ================================================================
    # 👨‍⚕️ PANEL DE DOCTOR
    # ================================================================
    elif st.session_state.rol == "Doctor":
        st.header("👨‍⚕️ Panel del Doctor — Revisión y Control de Pacientes")

        # 🔁 Refresco automático cada 10 segundos
        st_autorefresh(interval=10000, key="datarefresh")
        st.caption("🔄 La tabla se actualiza automáticamente cada 10 segundos.")

        try:
            conn = conectar()
            df = pd.read_sql("SELECT * FROM pre_triage", conn)
            conn.close()

            if not df.empty:
                with st.expander("🔍 Filtros"):
                    col1, col2, col3 = st.columns(3)
                    filtro_nombre = col1.text_input("Buscar por nombre")
                    filtro_prioridad = col2.selectbox("Filtrar por prioridad", ["Todos", "Baja", "Media", "Alta", "Inmediata"])
                    filtro_estado = col3.selectbox("Filtrar por estado", ["Todos", "Pendiente", "Atendido"])

                    if filtro_nombre:
                        df = df[df["Nombre"].str.contains(filtro_nombre, case=False, na=False)]
                    if filtro_prioridad != "Todos" and "Prioridad" in df.columns:
                        df = df[df["Prioridad"] == filtro_prioridad]
                    if filtro_estado != "Todos":
                        df = df[df["Estado"] == filtro_estado]

                st.dataframe(df, use_container_width=True)

                st.subheader("✏️ Actualizar Estado del Paciente")
                id_paciente = st.number_input("ID del registro a actualizar", min_value=1, step=1)
                nuevo_estado = st.selectbox("Nuevo estado", ["Pendiente", "Atendido"])

                if st.button("Actualizar registro"):
                    try:
                        conn = conectar()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE pre_triage SET Estado=%s WHERE id=%s",
                            (nuevo_estado, id_paciente)
                        )
                        conn.commit()
                        conn.close()
                        st.success("✅ Registro actualizado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al actualizar: {e}")
            else:
                st.info("ℹ️ No hay registros todavía.")
        except Exception as e:
            st.error(f"❌ Error al cargar los datos: {e}")
