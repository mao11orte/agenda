import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import os

# Importar capas DAL y BLL
import read as read
import process as process

# Inicializar la base de datos y datos semilla al arrancar la app
read.init_database()

# Configuración inicial de la página de Streamlit
st.set_page_config(
    page_title="VitalIS - Portal Médico de Salud",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# ESTILOS CSS PERSONALIZADOS - DISEÑO PREMIUM
# =====================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Configuración de tipografía global */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Encabezados con gradiente clínico */
    .main-title {
        background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .section-title {
        color: #0d9488;
        font-size: 1.8rem;
        font-weight: 600;
        border-bottom: 2px solid rgba(13, 148, 136, 0.1);
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    
    /* Tarjetas de Resumen KPI */
    .kpi-container {
        display: flex;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .kpi-card {
        flex: 1;
        background: rgba(15, 23, 42, 0.04);
        border: 1px solid rgba(13, 148, 136, 0.15);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        border-color: #0d9488;
        background: rgba(13, 148, 136, 0.02);
    }
    
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0d9488;
        margin: 5px 0;
    }
    
    .kpi-label {
        font-size: 0.95rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    /* Tarjeta de Recordatorio Especial */
    .reminder-card {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(13, 148, 136, 0.08) 100%);
        border: 1.5px solid rgba(2, 132, 199, 0.25);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.05);
    }
    
    .reminder-header {
        font-weight: 600;
        color: #0284c7;
        font-size: 1.15rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Cajas Clínicas para Formularios y Citas */
    .medical-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Etiquetas de Estado de Cita */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: capitalize;
    }
    
    .status-pendiente {
        background-color: #fef9c3;
        color: #a16207;
        border: 1px solid #fef08a;
    }
    
    .status-confirmada {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }
    
    .status-cancelada {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }
    
    .status-finalizada {
        background-color: #dbeafe;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# GESTIÓN DE ESTADOS DE SESIÓN (SESSION STATE)
# =====================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "patient" not in st.session_state:
    st.session_state.patient = None
if "view" not in st.session_state:
    st.session_state.view = "📊 Panel Principal"


def logout():
    st.session_state.logged_in = False
    st.session_state.patient = None
    st.session_state.view = "📊 Panel Principal"
    st.success("Sesión cerrada correctamente.")
    st.rerun()


# =====================================================================
# VISTA: INICIO DE SESIÓN Y REGISTRO (AUTENTICACIÓN)
# =====================================================================
def render_auth_view():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 40px;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#0d9488; font-weight:700; margin-bottom:5px;'>🩺 VitalIS</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#64748b; font-weight:400; margin-bottom:30px;'>Su Portal Médico e Historial Clínico Integrado</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse como Paciente"])
        
        # TAB 1: INICIO DE SESIÓN
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com").strip()
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
                submit_login = st.form_submit_button("Ingresar Seguro", use_container_width=True)
                
                if submit_login:
                    patient, msg = process.login_patient(email, password)
                    if patient:
                        st.session_state.logged_in = True
                        st.session_state.patient = patient
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        
        # TAB 2: REGISTRO DE PACIENTE NUEVO
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("register_form"):
                st.markdown("<h5 style='color:#0d9488;'>Información de Cuenta</h5>", unsafe_allow_html=True)
                reg_name = st.text_input("Nombre Completo *", placeholder="Juan Pérez").strip()
                reg_email = st.text_input("Correo Electrónico *", placeholder="juan.perez@correo.com").strip()
                reg_password = st.text_input("Contraseña Nueva *", type="password", placeholder="Mínimo 6 caracteres")
                
                st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                st.markdown("<h5 style='color:#0d9488;'>Información Médica y de Contacto</h5>", unsafe_allow_html=True)
                
                col_reg1, col_reg2 = st.columns(2)
                with col_reg1:
                    reg_phone = st.text_input("Teléfono Móvil", placeholder="+57 300 1234567")
                    reg_dob = st.date_input(
                        "Fecha de Nacimiento", 
                        min_value=date(1900, 1, 1), 
                        max_value=date.today(),
                        value=date(1990, 1, 1)
                    )
                with col_reg2:
                    reg_blood = st.selectbox("Grupo Sanguíneo", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "No definido"])
                    reg_allergies = st.text_input("Alergias Conocidas", placeholder="Ej: Penicilina, polen, ninguna", value="Ninguna")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit_register = st.form_submit_button("Crear mi Cuenta de Salud", use_container_width=True)
                
                if submit_register:
                    success, msg = process.register_patient(
                        name=reg_name,
                        email=reg_email,
                        password=reg_password,
                        phone=reg_phone,
                        date_of_birth=reg_dob.strftime("%Y-%m-%d"),
                        blood_type=reg_blood,
                        allergies=reg_allergies
                    )
                    if success:
                        st.success(msg)
                        st.info("Por favor, inicie sesión en la pestaña superior con sus credenciales registradas.")
                    else:
                        st.error(msg)


# =====================================================================
# VISTA: PANEL PRINCIPAL (DASHBOARD)
# =====================================================================
def render_dashboard(patient):
    st.markdown(f"<div class='main-title'>Portal de Salud Integrado</div>", unsafe_allow_html=True)
    st.markdown(f"<h4>Hola, <span style='color:#0d9488;'>{patient['name']}</span> 🩺 Bienvenido a su resumen médico en tiempo real.</h4>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calcular métricas usando Pandas en la BLL
    stats = process.get_patient_statistics(patient["id"])
    
    # 1. Alertas de Cita Próxima (Recordatorios)
    next_appt = stats["next_appointment"]
    if next_appt:
        # Calcular días restantes
        fecha_cita = datetime.strptime(next_appt["appointment_date"], "%Y-%m-%d").date()
        dias_restantes = (fecha_cita - date.today()).days
        
        tiempo_texto = f"hoy a las {next_appt['appointment_time']}" if dias_restantes == 0 else (
            f"mañana a las {next_appt['appointment_time']}" if dias_restantes == 1 else (
                f"en {dias_restantes} días ({next_appt['appointment_date']} a las {next_appt['appointment_time']})"
            )
        )
        
        st.markdown(f"""
        <div class='reminder-card'>
            <div class='reminder-header'>
                🔔 RECORDATORIO DE CITA ACTIVA
            </div>
            Su próxima consulta médica está programada para <b>{tiempo_texto}</b>.<br>
            <b>Médico:</b> {next_appt['doctor_name']} | <b>Especialidad:</b> {next_appt['specialty_name']}<br>
            <span style='font-size:0.9rem; color:#64748b;'>Por favor llegue 10 minutos antes y presente su documento de identidad.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 No tiene citas activas programadas en este momento. Puede agendar una nueva cita en el menú lateral.")

    # 2. Tarjetas KPI de Resumen Médico
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Citas Totales</div>
            <div class='kpi-value'>{stats['total_appointments']}</div>
            <div style='color:#64748b; font-size:0.85rem;'>Historial general registrado</div>
        </div>
        """, unsafe_allow_html=True)
    with col_kpi2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Especialidad más Consultada</div>
            <div class='kpi-value' style='font-size:1.6rem; padding:9px 0;'>{stats['most_visited_specialty']}</div>
            <div style='color:#64748b; font-size:0.85rem;'>Enfoque clínico principal</div>
        </div>
        """, unsafe_allow_html=True)
    with col_kpi3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Médico de Confianza</div>
            <div class='kpi-value' style='font-size:1.6rem; padding:9px 0;'>{stats['most_consulted_doctor']}</div>
            <div style='color:#64748b; font-size:0.85rem;'>Mayor frecuencia de consulta</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Gráficas Estadísticas y Tabla Rápida
    st.markdown("<h3 class='section-title'>📊 Estadísticas Clínicas</h3>", unsafe_allow_html=True)
    
    if stats["total_appointments"] > 0:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico de barras: Citas por Especialidad (Plotly)
            spec_counts = stats["specialty_counts"]
            if not spec_counts.empty:
                fig_spec = px.bar(
                    x=spec_counts.index,
                    y=spec_counts.values,
                    labels={'x': 'Especialidad', 'y': 'Número de Citas'},
                    title="Citas por Especialidad Médica (Histórico)",
                    color=spec_counts.values,
                    color_continuous_scale="Teal"
                )
                fig_spec.update_layout(coloraxis_showscale=False, height=320, margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig_spec, use_container_width=True)
            else:
                st.write("Sin datos de especialidades suficientes.")
                
        with col_g2:
            # Gráfico Donut de Estados de Citas
            df_appts = stats["appointments_df"]
            if not df_appts.empty:
                status_counts = df_appts["status"].value_counts()
                fig_status = px.pie(
                    names=status_counts.index,
                    values=status_counts.values,
                    title="Distribución del Estado de Citas",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_status.update_layout(height=320, margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig_status, use_container_width=True)
                
        # 4. Tabla de Citas Recientes
        st.markdown("<h3 class='section-title'>📅 Actividades Médicas Recientes</h3>", unsafe_allow_html=True)
        recientes = df_appts.head(3)
        
        for idx, row in recientes.iterrows():
            badge_class = f"status-{row['status']}"
            st.markdown(f"""
            <div class='medical-card' style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <b style='font-size:1.1rem; color:#0f172a;'>{row['specialty_name']}</b> - {row['doctor_name']}<br>
                    <span style='color:#64748b; font-size:0.9rem;'>Fecha: {row['appointment_date']} | Hora: {row['appointment_time']}</span>
                </div>
                <div>
                    <span class='status-badge {badge_class}'>{row['status']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se registran datos suficientes para graficar. Agende una cita médica para iniciar el análisis.")


# =====================================================================
# VISTA: MI PERFIL CLÍNICO
# =====================================================================
def render_profile(patient):
    st.markdown("<div class='main-title'>Mi Perfil Clínico</div>", unsafe_allow_html=True)
    st.markdown("Consulte y actualice su información básica de salud y de contacto.", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recargar datos frescos del paciente por si hubo cambios
    fresh_patient = read.get_patient_by_id(patient["id"])
    
    col_per1, col_per2 = st.columns([1, 2])
    
    with col_per1:
        st.markdown("""
        <div style='background: rgba(13, 148, 136, 0.05); border: 1.5px dashed #0d9488; border-radius: 12px; padding: 25px; text-align: center;'>
            <h1 style='font-size: 4rem; margin:0;'>👤</h1>
            <h3 style='color:#0d9488; margin-top:10px; margin-bottom:5px;'>Paciente Registrado</h3>
            <p style='color:#64748b; font-size:0.95rem; margin-bottom:20px;'>Cuenta de Salud Segura</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Grupo Sanguíneo:** `{fresh_patient['blood_type']}`")
        st.markdown(f"**Alergias:** `{fresh_patient['allergies']}`")
        st.markdown(f"**F. Nacimiento:** `{fresh_patient['date_of_birth']}`")
        st.markdown(f"**Contacto:** `{fresh_patient['phone']}`")
        
    with col_per2:
        st.markdown("<h3 class='section-title'>Actualizar Ficha Médica</h3>", unsafe_allow_html=True)
        
        with st.form("profile_update_form"):
            up_name = st.text_input("Nombre Completo *", value=fresh_patient["name"])
            
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                up_phone = st.text_input("Teléfono Móvil", value=fresh_patient["phone"])
                # Conversión de fecha de nacimiento de texto a objeto date para Streamlit
                try:
                    fecha_inicial = datetime.strptime(fresh_patient["date_of_birth"], "%Y-%m-%d").date()
                except ValueError:
                    fecha_inicial = date(1990, 1, 1)
                    
                up_dob = st.date_input("Fecha de Nacimiento", value=fecha_inicial, min_value=date(1900,1,1), max_value=date.today())
            with col_in2:
                sangre_lista = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "No definido"]
                sangre_idx = sangre_lista.index(fresh_patient["blood_type"]) if fresh_patient["blood_type"] in sangre_lista else 8
                up_blood = st.selectbox("Grupo Sanguíneo", sangre_lista, index=sangre_idx)
                up_allergies = st.text_input("Alergias Conocidas", value=fresh_patient["allergies"])
                
            submit_update = st.form_submit_button("Guardar Cambios Clínicos", use_container_width=True)
            
            if submit_update:
                success = read.update_patient(
                    patient_id=fresh_patient["id"],
                    name=up_name,
                    phone=up_phone,
                    date_of_birth=up_dob.strftime("%Y-%m-%d"),
                    blood_type=up_blood,
                    allergies=up_allergies
                )
                if success:
                    # Actualizar sesión con nuevos datos
                    st.session_state.patient = read.get_patient_by_id(fresh_patient["id"])
                    st.success("Ficha médica actualizada con éxito en la base de datos.")
                    st.rerun()
                else:
                    st.warning("No se detectaron cambios nuevos para guardar.")


# =====================================================================
# VISTA: AGENDA DE CITAS (CREACIÓN, EDICIÓN, CANCELACIÓN)
# =====================================================================
def render_appointments(patient):
    st.markdown("<div class='main-title'>Agenda de Citas Médicas</div>", unsafe_allow_html=True)
    st.markdown("Agende nuevas consultas médicas especializadas y gestione sus reservas activas.", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab_create, tab_manage = st.tabs(["📅 Agendar Nueva Cita", "📋 Administrar Citas Existentes"])
    
    # -----------------------------------------------------------------
    # TAB 1: CREACIÓN DE NUEVAS CITAS (CON PREVENCIÓN DE COLISIÓN)
    # -----------------------------------------------------------------
    with tab_create:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. Selector de Especialidad
        specialties = read.get_specialties()
        specialties_names = [s["name"] for s in specialties]
        
        selected_spec_name = st.selectbox("1. Seleccione la Especialidad Médica:", ["-- Seleccionar --"] + specialties_names)
        
        if selected_spec_name != "-- Seleccionar --":
            spec_id = next(s["id"] for s in specialties if s["name"] == selected_spec_name)
            
            # 2. Selector de Médico
            doctors = read.get_doctors_by_specialty(spec_id)
            if not doctors:
                st.warning("No hay médicos activos registrados en esta especialidad actualmente.")
            else:
                doctors_names = [d["name"] for d in doctors]
                selected_doc_name = st.selectbox("2. Seleccione el Especialista Médico:", ["-- Seleccionar --"] + doctors_names)
                
                if selected_doc_name != "-- Seleccionar --":
                    doctor_obj = next(d for d in doctors if d["name"] == selected_doc_name)
                    
                    # Rango de disponibilidad teórica del médico
                    horas_teoricas = [h.strip() for h in doctor_obj["availability_hours"].split(",")]
                    
                    col_sch1, col_sch2 = st.columns(2)
                    with col_sch1:
                        # 3. Selector de Fecha (Mañana en adelante por defecto)
                        fecha_seleccionada = st.date_input(
                            "3. Seleccione la Fecha de Consulta:",
                            min_value=date.today(),
                            value=date.today() + pd.Timedelta(days=1)
                        )
                    
                    # Cálculo inteligente de horas disponibles reales (evitando colisión)
                    citas_existentes_dia = read.get_appointments_by_doctor_and_date(doctor_obj["id"], fecha_seleccionada.strftime("%Y-%m-%d"))
                    horas_ocupadas = [c["appointment_time"] for c in citas_existentes_dia]
                    
                    # Si es hoy, filtrar horas pasadas
                    if fecha_seleccionada == date.today():
                        hora_actual = datetime.now().strftime("%H:%M")
                        horas_disponibles = [h for h in horas_teoricas if h not in horas_ocupadas and h > hora_actual]
                    else:
                        horas_disponibles = [h for h in horas_teoricas if h not in horas_ocupadas]
                        
                    with col_sch2:
                        # 4. Selector de Hora Libre
                        if not horas_disponibles:
                            st.error("⚠️ El médico no cuenta con horarios libres para la fecha seleccionada. Intente otra fecha.")
                            selected_time = None
                        else:
                            selected_time = st.selectbox("4. Seleccione la Hora de Consulta:", horas_disponibles)
                            
                    st.markdown("<br>", unsafe_allow_html=True)
                    notes = st.text_area("Observaciones o Síntomas (Opcional):", placeholder="Describa brevemente el motivo de la consulta...")
                    
                    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
                    
                    # Botón de Confirmación
                    agendar_btn = st.button("Confirmar Agendamiento Médico", type="primary", use_container_width=True)
                    
                    if agendar_btn and selected_time:
                        # Doble validación en la Capa de Lógica de Negocio
                        valido, msg_error = process.validate_appointment(
                            patient_id=patient["id"],
                            doctor_id=doctor_obj["id"],
                            date_obj=fecha_seleccionada,
                            time_str=selected_time
                        )
                        
                        if valido:
                            read.create_appointment(
                                patient_id=patient["id"],
                                doctor_id=doctor_obj["id"],
                                appointment_date=fecha_seleccionada.strftime("%Y-%m-%d"),
                                appointment_time=selected_time,
                                status="pendiente",
                                notes=notes
                            )
                            st.success(f"¡Cita agendada con éxito! Su cita con el {doctor_obj['name']} ha sido guardada en estado PENDIENTE.")
                            st.balloons()
                        else:
                            st.error(f"Error de validación médica: {msg_error}")
                            
    # -----------------------------------------------------------------
    # TAB 2: ADMINISTRAR CITAS EXISTENTES (VER, REPROGRAMAR, CANCELAR)
    # -----------------------------------------------------------------
    with tab_manage:
        st.markdown("<br>", unsafe_allow_html=True)
        
        appointments = read.get_appointments_by_patient(patient["id"])
        
        if not appointments:
            st.info("No cuenta con citas médicas registradas en su historial.")
        else:
            # Organizar en base de acordeones o cards dinámicas por estado
            for appt in appointments:
                # Determinar estilos visuales según el estado de la cita
                badge_class = f"status-{appt['status']}"
                
                with st.container():
                    st.markdown(f"""
                    <div class='medical-card'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <b style='font-size:1.2rem; color:#0f172a;'>{appt['specialty_name']}</b> - {appt['doctor_name']}<br>
                                <span style='color:#64748b;'><b>Fecha:</b> {appt['appointment_date']} | <b>Hora:</b> {appt['appointment_time']}</span>
                            </div>
                            <div>
                                <span class='status-badge {badge_class}'>{appt['status']}</span>
                            </div>
                        </div>
                        <div style='margin-top:10px; color:#475569; font-size:0.95rem; background:rgba(0,0,0,0.01); padding:8px; border-radius:6px; border-left:3px solid #cbd5e1;'>
                            <b>Observaciones:</b> {appt['notes'] if appt['notes'] else 'Sin observaciones ingresadas.'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Acciones permitidas solo para citas 'pendiente' y 'confirmada'
                    if appt["status"] in ["pendiente", "confirmada"]:
                        col_btn1, col_btn2 = st.columns([1, 4])
                        
                        # 1. CANCELACIÓN
                        with col_btn1:
                            cancelar_confirm = st.button("❌ Cancelar Cita", key=f"canc_{appt['id']}", use_container_width=True)
                            if cancelar_confirm:
                                if read.update_appointment_status(appt["id"], "cancelada"):
                                    st.success(f"La cita para {appt['specialty_name']} ha sido cancelada.")
                                    st.rerun()
                                    
                        # 2. REPROGRAMACIÓN
                        with col_btn2:
                            with st.expander("🔄 Reprogramar esta Cita"):
                                col_rep1, col_rep2 = st.columns(2)
                                
                                doctor_detail = read.get_doctor_by_id(appt["doctor_id"])
                                horas_teoricas = [h.strip() for h in doctor_detail["availability_hours"].split(",")]
                                
                                with col_rep1:
                                    nueva_fecha = st.date_input(
                                        "Nueva Fecha:",
                                        min_value=date.today(),
                                        value=datetime.strptime(appt["appointment_date"], "%Y-%m-%d").date(),
                                        key=f"f_rep_{appt['id']}"
                                    )
                                
                                # Filtrar horas ya agendadas de ese médico
                                citas_existentes_dia = read.get_appointments_by_doctor_and_date(appt["doctor_id"], nueva_fecha.strftime("%Y-%m-%d"))
                                horas_ocupadas = [c["appointment_time"] for c in citas_existentes_dia if c["id"] != appt["id"]]
                                
                                if nueva_fecha == date.today():
                                    hora_actual = datetime.now().strftime("%H:%M")
                                    horas_disponibles = [h for h in horas_teoricas if h not in horas_ocupadas and h > hora_actual]
                                else:
                                    horas_disponibles = [h for h in horas_teoricas if h not in horas_ocupadas]
                                    
                                with col_rep2:
                                    if not horas_disponibles:
                                        st.error("Sin disponibilidad médica para esta fecha.")
                                        nueva_hora = None
                                    else:
                                        # Seleccionar hora por defecto si existe en la nueva lista
                                        def_idx = horas_disponibles.index(appt["appointment_time"]) if appt["appointment_time"] in horas_disponibles else 0
                                        nueva_hora = st.selectbox("Nueva Hora:", horas_disponibles, index=def_idx, key=f"h_rep_{appt['id']}")
                                        
                                nueva_nota = st.text_input("Actualizar observaciones:", value=appt["notes"], key=f"n_rep_{appt['id']}")
                                
                                rep_submit = st.button("Confirmar Reprogramación", key=f"btn_rep_{appt['id']}")
                                if rep_submit and nueva_hora:
                                    # Lógica de validación
                                    valido, msg_error = process.validate_appointment(
                                        patient_id=patient["id"],
                                        doctor_id=appt["doctor_id"],
                                        date_obj=nueva_fecha,
                                        time_str=nueva_hora,
                                        appointment_id=appt["id"]
                                    )
                                    
                                    if valido:
                                        read.update_appointment(
                                            appointment_id=appt["id"],
                                            doctor_id=appt["doctor_id"],
                                            appointment_date=nueva_fecha.strftime("%Y-%m-%d"),
                                            appointment_time=nueva_hora,
                                            notes=nueva_nota
                                        )
                                        st.success("La cita ha sido reprogramada con éxito.")
                                        st.rerun()
                                    else:
                                        st.error(f"Imposible reprogramar: {msg_error}")
                    st.markdown("<br>", unsafe_allow_html=True)


# =====================================================================
# VISTA: RECETAS Y FÓRMULAS MÉDICAS
# =====================================================================
def render_formulas(patient):
    st.markdown("<div class='main-title'>Fórmulas y Recetas Médicas</div>", unsafe_allow_html=True)
    st.markdown("Consulte el histórico cronológico de sus prescripciones médicas ordenado por especialidad.", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    formulas = read.get_formulas_by_patient(patient["id"])
    
    if not formulas:
        st.info("No se registran fórmulas médicas en su expediente.")
    else:
        # Barra de búsqueda
        search_query = st.text_input("🔍 Buscar fórmulas por Especialista o Medicamento:", placeholder="Ej: Acetaminofén, CeraVe, Alejandro Ríos...")
        
        filtered_formulas = formulas
        if search_query:
            q = search_query.lower()
            filtered_formulas = [
                f for f in formulas
                if q in f["doctor_name"].lower()
                or q in f["specialty_name"].lower()
                or q in f["medications"].lower()
            ]
            
        if not filtered_formulas:
            st.warning("No se encontraron fórmulas médicas que coincidan con la búsqueda.")
        else:
            for form in filtered_formulas:
                st.markdown(f"""
                <div class='medical-card'>
                    <div style='background-color:#0d9488; color:white; padding:10px 15px; border-radius:8px 8px 0 0; margin:-20px -20px 15px -20px; display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-weight:600; font-size:1.1rem;'>📄 Receta: {form['specialty_name']}</span>
                        <span style='font-size:0.9rem;'>Fecha de Emisión: {form['issue_date']}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <div>
                            <b>Médico Prescriptor:</b> {form['doctor_name']}<br>
                            <span style='font-size:0.9rem; color:#64748b;'>Especialidad: {form['specialty_name']}</span>
                        </div>
                    </div>
                    <hr style='margin:12px 0; border:0; border-top:1px solid #e2e8f0;'>
                    <div style='margin-bottom:12px;'>
                        <h5 style='color:#0f172a; font-weight:600; margin-bottom:5px;'>💊 Medicamentos Prescritos:</h5>
                        <p style='white-space: pre-line; color:#334155; font-size:0.95rem; background:rgba(0,0,0,0.01); padding:10px; border-radius:6px; border-left:3px solid #0d9488;'>{form['medications']}</p>
                    </div>
                    <div>
                        <h5 style='color:#0f172a; font-weight:600; margin-bottom:5px;'>📋 Instrucciones de Consumo:</h5>
                        <p style='white-space: pre-line; color:#334155; font-size:0.95rem; background:rgba(0,0,0,0.01); padding:10px; border-radius:6px; border-left:3px solid #0284c7;'>{form['instructions'] if form['instructions'] else 'Seguir dosis estándar.'}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)


# =====================================================================
# VISTA: HISTORIAL Y CARGA DE EXÁMENES CLÍNICOS (PDFs)
# =====================================================================
def render_exams(patient):
    st.markdown("<div class='main-title'>Exámenes y Resultados Clínicos</div>", unsafe_allow_html=True)
    st.markdown("Suba de forma segura sus resultados de laboratorio, análisis clínicos o radiografías en formato PDF.", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_ex1, col_ex2 = st.columns([1, 2])
    
    # 1. Formulario de Carga
    with col_ex1:
        st.markdown("<h3 class='section-title'>📁 Cargar Nuevo Examen</h3>", unsafe_allow_html=True)
        
        with st.form("exam_upload_form", clear_on_submit=True):
            exam_name = st.text_input("Nombre del Examen / Análisis *", placeholder="Ej: Perfil Lipídico, Resonancia")
            uploaded_file = st.file_uploader("Seleccione el archivo (Únicamente PDF) *", type=["pdf"])
            notes = st.text_area("Notas Clínicas Adicionales:", placeholder="Ej: Dr. Alejandro solicitó este análisis para el colesterol...")
            
            submit_exam = st.form_submit_button("Subir e Integrar al Historial")
            
            if submit_exam:
                success, msg = process.save_clinical_exam(
                    patient_id=patient["id"],
                    exam_name=exam_name,
                    uploaded_file=uploaded_file,
                    notes=notes
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
    # 2. Historial de Exámenes Cargados
    with col_ex2:
        st.markdown("<h3 class='section-title'>📋 Historial de Documentos</h3>", unsafe_allow_html=True)
        
        exams = read.get_exams_by_patient(patient["id"])
        
        if not exams:
            st.info("No se registran documentos o exámenes clínicos PDF cargados en su cuenta.")
        else:
            for ex in exams:
                # Obtener la ruta completa para leer el archivo y permitir descarga
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                full_path = os.path.join(base_dir, ex["file_path"])
                
                file_available = os.path.exists(full_path)
                
                with st.container():
                    st.markdown(f"""
                    <div class='medical-card'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <b style='font-size:1.15rem; color:#0f172a;'>📄 {ex['exam_name']}</b><br>
                                <span style='color:#64748b; font-size:0.85rem;'>Fecha de Carga: {ex['upload_date']}</span>
                            </div>
                        </div>
                        <div style='margin-top:8px; font-size:0.9rem; color:#475569;'>
                            <b>Detalles:</b> {ex['notes'] if ex['notes'] else 'Sin observaciones adicionales.'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_ex_action1, col_ex_action2 = st.columns([1, 1])
                    
                    # Botón de Descarga Segura Nativo
                    with col_ex_action1:
                        if file_available:
                            try:
                                with open(full_path, "rb") as f:
                                    pdf_bytes = f.read()
                                st.download_button(
                                    label="⬇️ Descargar PDF",
                                    data=pdf_bytes,
                                    file_name=f"{ex['exam_name'].replace(' ', '_')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_{ex['id']}",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error("Error al leer archivo.")
                        else:
                            st.warning("⚠️ Archivo físico no encontrado.")
                            
                    # Botón de Eliminación
                    with col_ex_action2:
                        del_btn = st.button("🗑️ Eliminar Examen", key=f"del_{ex['id']}", use_container_width=True)
                        if del_btn:
                            success, msg = process.delete_clinical_exam(ex["id"], patient["id"])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                st.markdown("<br>", unsafe_allow_html=True)


# =====================================================================
# MOTOR PRINCIPAL Y NAVEGACIÓN LATERAL (SIDEBAR)
# =====================================================================
def main():
    if not st.session_state.logged_in:
        render_auth_view()
    else:
        patient = st.session_state.patient
        
        # Barra lateral de Navegación Premium
        st.sidebar.markdown(f"""
        <div style='text-align: center; padding: 15px 0;'>
            <h2 style='color:#0d9488; font-weight:700; margin:0;'>🩺 VitalIS</h2>
            <p style='color:#64748b; font-size:0.85rem; margin-top:3px;'>Portal Médico e Historial Clínico</p>
        </div>
        <hr style='margin: 0 0 15px 0;'>
        <div style='background: rgba(13, 148, 136, 0.05); border-radius:10px; padding:12px; margin-bottom:20px; border-left: 4px solid #0d9488;'>
            <span style='font-size:0.85rem; color:#64748b;'>PACIENTE ACTIVO</span><br>
            <b style='font-size:1.05rem; color:#0f172a;'>{patient['name']}</b><br>
            <span style='font-size:0.85rem; color:#64748b;'>📧 {patient['email']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Selector de Vistas Principal
        opciones = [
            "📊 Panel Principal",
            "👤 Mi Perfil Clínico",
            "📅 Agenda de Citas",
            "📝 Recetas y Fórmulas",
            "📁 Exámenes Clínicos (PDF)"
        ]
        
        selected_view = st.sidebar.radio("Navegación del Portal", opciones)
        st.session_state.view = selected_view
        
        # Información médica rápida en sidebar
        st.sidebar.markdown("""
        <hr style='margin: 15px 0;'>
        <div style='font-size:0.9rem; color:#475569;'>
            <b>📞 Soporte VitalIS:</b> +1 800 123 456<br>
            <b>⏰ Emergencias:</b> Línea Nacional 123
        </div>
        """, unsafe_allow_html=True)
        
        # Botón para cerrar sesión
        st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
        if st.sidebar.button("🔐 Cerrar Sesión Segura", use_container_width=True):
            logout()
            
        # Renderizar la vista seleccionada
        if st.session_state.view == "📊 Panel Principal":
            render_dashboard(patient)
        elif st.session_state.view == "👤 Mi Perfil Clínico":
            render_profile(patient)
        elif st.session_state.view == "📅 Agenda de Citas":
            render_appointments(patient)
        elif st.session_state.view == "📝 Recetas y Fórmulas":
            render_formulas(patient)
        elif st.session_state.view == "📁 Exámenes Clínicos (PDF)":
            render_exams(patient)

if __name__ == "__main__":
    main()
