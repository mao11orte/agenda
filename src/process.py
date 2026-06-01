import os
import uuid
import hashlib
import pandas as pd
from datetime import datetime, date
import read as read

# Carpeta para archivos PDF de exámenes
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

# =====================================================================
# SEGURIDAD Y AUTENTICACIÓN
# =====================================================================

def hash_password(password):
    """Cifra una contraseña usando SHA-256 con un salt dinámico."""
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password, stored_hash):
    """Compara una contraseña con el hash guardado."""
    if not stored_hash or ":" not in stored_hash:
        return False
    salt, hashed = stored_hash.split(":")
    check_hash = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return check_hash == hashed

def register_patient(name, email, password, phone, date_of_birth, blood_type, allergies):
    """
    Registra un nuevo paciente en el sistema, encriptando su contraseña
    y autogenerando un historial semilla ficticio para demostración premium.
    """
    if not name or not email or not password:
        return False, "Por favor complete todos los campos obligatorios (Nombre, Correo, Contraseña)."
    
    if "@" not in email or "." not in email:
        return False, "Formato de correo electrónico inválido."
        
    password_hashed = hash_password(password)
    
    patient_id = read.create_patient(
        name=name,
        email=email,
        password_hash=password_hashed,
        phone=phone,
        date_of_birth=date_of_birth,
        blood_type=blood_type,
        allergies=allergies
    )
    
    if patient_id is None:
        return False, "El correo electrónico ya se encuentra registrado."
        
    # Crear automáticamente historial de prueba (citas finalizadas y fórmulas)
    seed_patient_history(patient_id)
    
    return True, "Registro exitoso. ¡Bienvenido a su Portal de Salud!"

def login_patient(email, password):
    """Verifica las credenciales de inicio de sesión."""
    if not email or not password:
        return None, "Por favor complete el correo y la contraseña."
        
    patient = read.get_patient_by_email(email)
    if not patient:
        return None, "Correo electrónico o contraseña incorrectos."
        
    if verify_password(password, patient["password_hash"]):
        return patient, "Inicio de sesión exitoso."
    else:
        return None, "Correo electrónico o contraseña incorrectos."


# =====================================================================
# LÓGICA DE NEGOCIO: VALIDACIÓN DE CITAS
# =====================================================================

def validate_appointment(patient_id, doctor_id, date_obj, time_str, appointment_id=None):
    """
    Valida las reglas de negocio para agendar o reprogramar una cita médica.
    Retorna (True, "") si es válida, o (False, "Motivo") si infringe alguna regla.
    """
    hoy = date.today()
    
    # 1. Validar que la fecha sea futura
    if date_obj < hoy:
        return False, "No es posible agendar citas en fechas pasadas."
    if date_obj == hoy:
        # Si es hoy, verificar que la hora no haya pasado
        hora_actual = datetime.now().strftime("%H:%M")
        if time_str <= hora_actual:
            return False, "La hora seleccionada para el día de hoy ya ha transcurrido."

    # 2. Validar que el médico esté disponible en esa hora (revisar su agenda teórica)
    doctor = read.get_doctor_by_id(doctor_id)
    if not doctor:
        return False, "El médico seleccionado no existe en el sistema."
        
    disponibles = [h.strip() for h in doctor["availability_hours"].split(",")]
    if time_str not in disponibles:
        return False, f"El médico {doctor['name']} no atiende a las {time_str}."

    date_str = date_obj.strftime("%Y-%m-%d")

    # 3. Validar colisión de horarios del médico en la Base de Datos
    citas_medico = read.get_appointments_by_doctor_and_date(doctor_id, date_str)
    for cita in citas_medico:
        if cita["appointment_time"] == time_str:
            # Si estamos editando una cita existente, ignoramos la colisión con ella misma
            if appointment_id is not None and cita["id"] == int(appointment_id):
                continue
            return False, f"El horario de las {time_str} ya se encuentra reservado para el médico {doctor['name']}."

    # 4. Validar colisión de horarios del propio paciente (no agendar dos citas a la misma hora)
    citas_paciente = read.get_appointments_by_patient(patient_id)
    for cita in citas_paciente:
        if cita["appointment_date"] == date_str and cita["appointment_time"] == time_str and cita["status"] != "cancelada":
            if appointment_id is not None and cita["id"] == int(appointment_id):
                continue
            return False, f"Ya tiene otra cita médica agendada para el {date_str} a las {time_str} ({cita['specialty_name']})."

    return True, ""


# =====================================================================
# ANALÍTICAS Y ESTADÍSTICAS DEL PACIENTE
# =====================================================================

def get_patient_statistics(patient_id):
    """
    Calcula analíticas y resúmenes estadísticos sobre el paciente usando Pandas.
    Retorna un diccionario estructurado listo para la interfaz visual.
    """
    appointments = read.get_appointments_by_patient(patient_id)
    
    default_stats = {
        "total_appointments": 0,
        "active_appointments": 0,
        "completed_appointments": 0,
        "cancelled_appointments": 0,
        "most_visited_specialty": "Ninguna",
        "most_consulted_doctor": "Ninguno",
        "specialty_counts": pd.Series(dtype=int),
        "doctor_counts": pd.Series(dtype=int),
        "appointments_df": pd.DataFrame(),
        "next_appointment": None
    }
    
    if not appointments:
        return default_stats
        
    df = pd.DataFrame(appointments)
    
    # Calcular contadores generales
    total = len(df)
    active = len(df[df["status"].isin(["pendiente", "confirmada"])])
    completed = len(df[df["status"] == "finalizada"])
    cancelled = len(df[df["status"] == "cancelada"])
    
    # Especialidad más visitada (ignorar canceladas para estadísticas médicas válidas)
    df_validas = df[df["status"] != "cancelada"]
    
    most_visited_spec = "Ninguna"
    spec_counts = pd.Series(dtype=int)
    if not df_validas.empty and "specialty_name" in df_validas.columns:
        spec_counts = df_validas["specialty_name"].value_counts()
        most_visited_spec = spec_counts.index[0]
        
    # Médico más consultado
    most_consulted_doc = "Ninguno"
    doc_counts = pd.Series(dtype=int)
    if not df_validas.empty and "doctor_name" in df_validas.columns:
        doc_counts = df_validas["doctor_name"].value_counts()
        most_consulted_doc = doc_counts.index[0]
        
    # Buscar la próxima cita activa (fecha futura, estado activo)
    hoy_str = date.today().strftime("%Y-%m-%d")
    hora_actual = datetime.now().strftime("%H:%M")
    
    df_activas = df[df["status"].isin(["pendiente", "confirmada"])]
    next_appt = None
    
    if not df_activas.empty:
        # Filtrar futuras o de hoy más tarde
        df_futuras = df_activas[
            (df_activas["appointment_date"] > hoy_str) | 
            ((df_activas["appointment_date"] == hoy_str) & (df_activas["appointment_time"] >= hora_actual))
        ]
        if not df_futuras.empty:
            # Ordenar por fecha y hora ascendente
            df_ordenado = df_futuras.sort_values(by=["appointment_date", "appointment_time"], ascending=True)
            next_appt = df_ordenado.iloc[0].to_dict()
            
    return {
        "total_appointments": total,
        "active_appointments": active,
        "completed_appointments": completed,
        "cancelled_appointments": cancelled,
        "most_visited_specialty": most_visited_spec,
        "most_consulted_doctor": most_consulted_doc,
        "specialty_counts": spec_counts,
        "doctor_counts": doc_counts,
        "appointments_df": df,
        "next_appointment": next_appt
    }


# =====================================================================
# GESTIÓN DE EXÁMENES Y ARCHIVOS
# =====================================================================

def save_clinical_exam(patient_id, exam_name, uploaded_file, notes=""):
    """
    Sube y guarda un PDF de examen en el disco local y lo registra en la base de datos.
    Retorna (True, "Mensaje") o (False, "Error").
    """
    if not exam_name:
        return False, "Debe ingresar el nombre descriptivo del examen."
        
    if uploaded_file is None:
        return False, "Por favor seleccione un archivo PDF."
        
    if not uploaded_file.name.lower().endswith(".pdf"):
        return False, "Únicamente se permiten archivos en formato PDF para exámenes médicos."
        
    try:
        # Asegurar directorio físico de subidas
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generar nombre físico seguro
        file_extension = ".pdf"
        unique_filename = f"exam_{patient_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Guardar en disco
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Registrar en la base de datos
        hoy_str = date.today().strftime("%Y-%m-%d")
        # Guardamos la ruta relativa para mayor portabilidad del código
        relative_path = os.path.join("uploads", unique_filename)
        
        read.create_exam(
            patient_id=patient_id,
            exam_name=exam_name,
            upload_date=hoy_str,
            file_path=relative_path,
            notes=notes
        )
        
        return True, "El examen clínico ha sido guardado y cargado satisfactoriamente."
    except Exception as e:
        return False, f"Error al procesar el archivo físico: {str(e)}"

def delete_clinical_exam(exam_id, patient_id):
    """
    Elimina el registro de un examen médico y remueve el archivo del almacenamiento físico.
    """
    relative_path = read.delete_exam(exam_id, patient_id)
    if relative_path:
        # Intentar remover físicamente
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, relative_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass # Ignorar fallo si el archivo ya no existía en disco
        return True, "Documento clínico eliminado del historial."
    return False, "No se encontró el archivo clínico a eliminar."


# =====================================================================
# DATA SEMILLA INTERNA PARA PACIENTES NUEVOS
# =====================================================================

def seed_patient_history(patient_id):
    """
    Crea un historial clínico semilla (1 cita finalizada + 1 fórmula médica) 
    para que la plataforma no empiece completamente vacía y el usuario experimente 
    el portal con información enriquecida inmediatamente.
    """
    try:
        # Cargar médicos
        doctors = read.get_all_doctors()
        if not doctors:
            return
            
        # Tomar Dr. Alejandro Ríos (Medicina General) e Dra. Isabel Londoño (Dermatología)
        dr_general = next((d for d in doctors if "Alejandro" in d["name"]), doctors[0])
        dr_derma = next((d for d in doctors if "Isabel" in d["name"]), doctors[-1])
        
        # 1. Cita Finalizada - Medicina General (Hace 10 días)
        fecha_general = (datetime.now() - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
        appt_id1 = read.create_appointment(
            patient_id=patient_id,
            doctor_id=dr_general["id"],
            appointment_date=fecha_general,
            appointment_time="09:00",
            status="finalizada",
            notes="Paciente asiste a consulta general por chequeo de rutina. Reporta leves dolores de cabeza ocasionales. Signos vitales normales."
        )
        
        # Fórmula médica de esa cita
        read.create_formula(
            appointment_id=appt_id1,
            patient_id=patient_id,
            doctor_id=dr_general["id"],
            issue_date=fecha_general,
            medications="1. Acetaminofén 500mg (Tabletas)\n2. Hidratación regular (Suplemento electrolitos)",
            instructions="Tomar 1 tableta de Acetaminofén cada 8 horas únicamente en caso de dolor de cabeza fuerte. Beber 2 litros de agua diarios."
        )

        # 2. Cita Finalizada - Dermatología (Hace 3 días)
        fecha_derma = (datetime.now() - pd.Timedelta(days=3)).strftime("%Y-%m-%d")
        appt_id2 = read.create_appointment(
            patient_id=patient_id,
            doctor_id=dr_derma["id"],
            appointment_date=fecha_derma,
            appointment_time="11:00",
            status="finalizada",
            notes="Consulta dermatológica por resequedad severa en rostro debido al cambio de clima de la temporada."
        )
        
        # Fórmula dermatológica
        read.create_formula(
            appointment_id=appt_id2,
            patient_id=patient_id,
            doctor_id=dr_derma["id"],
            issue_date=fecha_derma,
            medications="1. Crema hidratante facial con Ceramidas (CeraVe o similar)\n2. Protector Solar FPS 50+ en gel",
            instructions="Aplicar crema hidratante por la mañana y noche sobre el rostro limpio. Aplicar protector solar facial cada 4 horas durante el día."
        )
    except Exception:
        pass # Silenciar fallos para no interrumpir el registro principal del paciente
