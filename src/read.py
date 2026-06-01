import sqlite3
import os
from datetime import datetime

# Ruta de la base de datos relacional
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")

def get_connection():
    """Retorna una conexión activa a la base de datos SQLite con soporte para llaves foráneas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

def init_database():
    """Inicializa la base de datos creando todas las tablas del modelo de datos si no existen."""
    # Asegurar que el directorio de la BD existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Tabla de Especialidades Médicas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS specialties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
        """)
        
        # 2. Tabla de Médicos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            availability_hours TEXT NOT NULL, -- Almacenará horas separadas por comas (ej. "08:00,09:00,10:00")
            FOREIGN KEY (specialty_id) REFERENCES specialties(id) ON DELETE CASCADE
        );
        """)
        
        # 3. Tabla de Pacientes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT,
            date_of_birth TEXT,
            blood_type TEXT,
            allergies TEXT
        );
        """)
        
        # 4. Tabla de Citas Médicas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,  -- YYYY-MM-DD
            appointment_time TEXT NOT NULL,  -- HH:MM
            status TEXT NOT NULL CHECK(status IN ('pendiente', 'confirmada', 'cancelada', 'finalizada')),
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
        );
        """)
        
        # 5. Tabla de Fórmulas Médicas (Recetas)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL, -- YYYY-MM-DD
            medications TEXT NOT NULL, -- JSON o Texto detallado
            instructions TEXT,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
        );
        """)
        
        # 6. Tabla de Exámenes Médicos / Documentos PDF
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            upload_date TEXT NOT NULL, -- YYYY-MM-DD
            file_path TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
        """)
        
        conn.commit()
    
    # Rellenar con datos iniciales de médicos y especialidades
    seed_database()

def seed_database():
    """Llena la base de datos con especialidades y médicos semilla si están vacíos."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si ya existen especialidades
        cursor.execute("SELECT COUNT(*) FROM specialties;")
        if cursor.fetchone()[0] == 0:
            specialties_data = [
                ("Medicina General", "Atención primaria, prevención y diagnóstico clínico general."),
                ("Pediatría", "Cuidado integral y desarrollo médico de bebés, niños y adolescentes."),
                ("Cardiología", "Prevención, diagnóstico y tratamiento de enfermedades cardiovasculares."),
                ("Dermatología", "Diagnóstico y tratamiento de patologías de la piel, cabello y uñas."),
                ("Ginecología", "Cuidado del sistema reproductor femenino y salud de la mujer."),
                ("Traumatología", "Tratamiento de lesiones del aparato locomotor (huesos, músculos y articulaciones).")
            ]
            cursor.executemany("INSERT INTO specialties (name, description) VALUES (?, ?);", specialties_data)
            conn.commit()
            
        # Verificar si ya existen médicos
        cursor.execute("SELECT COUNT(*) FROM doctors;")
        if cursor.fetchone()[0] == 0:
            # Obtener IDs de las especialidades insertadas
            cursor.execute("SELECT id, name FROM specialties;")
            spec_map = {row["name"]: row["id"] for row in cursor.fetchall()}
            
            doctors_data = [
                ("Dr. Alejandro Ríos", spec_map["Medicina General"], "alejandro.rios@salud.com", "08:00,09:00,10:00,11:00,14:00,15:00,16:00"),
                ("Dra. Sofía Castro", spec_map["Pediatría"], "sofia.castro@salud.com", "09:00,10:00,11:00,14:00,15:00,16:00"),
                ("Dr. Martín Altamirano", spec_map["Cardiología"], "martin.alta@salud.com", "08:00,10:00,11:00,14:00,16:00"),
                ("Dra. Isabel Londoño", spec_map["Dermatología"], "isabel.londono@salud.com", "09:00,11:00,14:00,15:00,17:00"),
                ("Dra. Clara Valencia", spec_map["Ginecología"], "clara.valencia@salud.com", "08:00,09:00,10:00,13:00,14:00,15:00"),
                ("Dr. Roberto Méndez", spec_map["Traumatología"], "roberto.mendez@salud.com", "10:00,11:00,15:00,16:00,17:00")
            ]
            cursor.executemany("INSERT INTO doctors (name, specialty_id, email, availability_hours) VALUES (?, ?, ?, ?);", doctors_data)
            conn.commit()


# =====================================================================
# OPERACIONES CRUD - PACIENTES (PATIENTS)
# =====================================================================

def create_patient(name, email, password_hash, phone="", date_of_birth="", blood_type="No definido", allergies="Ninguna"):
    """Registra un nuevo paciente en el sistema."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (name, email, password_hash, phone, date_of_birth, blood_type, allergies)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (name, email, password_hash, phone, date_of_birth, blood_type, allergies))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # El correo ya está registrado

def get_patient_by_email(email):
    """Busca un paciente por su correo electrónico."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE email = ?;", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_patient_by_id(patient_id):
    """Busca un paciente por su ID único."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ?;", (patient_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_patient(patient_id, name, phone, date_of_birth, blood_type, allergies):
    """Actualiza la información personal y médica de un paciente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients
            SET name = ?, phone = ?, date_of_birth = ?, blood_type = ?, allergies = ?
            WHERE id = ?;
        """, (name, phone, date_of_birth, blood_type, allergies, patient_id))
        conn.commit()
        return cursor.rowcount > 0


# =====================================================================
# OPERACIONES CRUD - ESPECIALIDADES Y MÉDICOS
# =====================================================================

def get_specialties():
    """Retorna todas las especialidades disponibles."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM specialties ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]

def get_doctors_by_specialty(specialty_id):
    """Retorna los médicos asignados a una especialidad."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors WHERE specialty_id = ? ORDER BY name ASC;", (specialty_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_doctor_by_id(doctor_id):
    """Retorna la información detallada de un médico por su ID, incluyendo su especialidad."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, s.name as specialty_name 
            FROM doctors d
            JOIN specialties s ON d.specialty_id = s.id
            WHERE d.id = ?;
        """, (doctor_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_doctors():
    """Retorna todos los médicos registrados con sus especialidades."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, s.name as specialty_name 
            FROM doctors d
            JOIN specialties s ON d.specialty_id = s.id
            ORDER BY d.name ASC;
        """)
        return [dict(row) for row in cursor.fetchall()]


# =====================================================================
# OPERACIONES CRUD - CITAS MÉDICAS (APPOINTMENTS)
# =====================================================================

def create_appointment(patient_id, doctor_id, appointment_date, appointment_time, status="pendiente", notes=""):
    """Registra una nueva cita médica."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (patient_id, doctor_id, appointment_date, appointment_time, status, notes))
        conn.commit()
        return cursor.lastrowid

def get_appointments_by_patient(patient_id):
    """Retorna todas las citas del paciente, ordenadas de la más reciente a la más antigua."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, d.name as doctor_name, s.name as specialty_name, d.email as doctor_email
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN specialties s ON d.specialty_id = s.id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC;
        """, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_appointments_by_doctor_and_date(doctor_id, appointment_date):
    """Retorna las citas agendadas de un médico en una fecha específica."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelada';
        """, (doctor_id, appointment_date))
        return [dict(row) for row in cursor.fetchall()]

def update_appointment_status(appointment_id, status):
    """Actualiza el estado de una cita ('pendiente', 'confirmada', 'cancelada', 'finalizada')."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET status = ? WHERE id = ?;", (status, appointment_id))
        conn.commit()
        return cursor.rowcount > 0

def update_appointment(appointment_id, doctor_id, appointment_date, appointment_time, notes):
    """Permite reprogramar una cita y editar sus notas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET doctor_id = ?, appointment_date = ?, appointment_time = ?, notes = ?, status = 'pendiente'
            WHERE id = ?;
        """, (doctor_id, appointment_date, appointment_time, notes, appointment_id))
        conn.commit()
        return cursor.rowcount > 0


# =====================================================================
# OPERACIONES CRUD - FÓRMULAS MÉDICAS (RECETAS)
# =====================================================================

def create_formula(appointment_id, patient_id, doctor_id, issue_date, medications, instructions=""):
    """Crea una fórmula médica asociada a un paciente y opcionalmente a una cita."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medical_formulas (appointment_id, patient_id, doctor_id, issue_date, medications, instructions)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (appointment_id, patient_id, doctor_id, issue_date, medications, instructions))
        conn.commit()
        return cursor.lastrowid

def get_formulas_by_patient(patient_id):
    """Retorna todas las fórmulas médicas de un paciente ordenadas cronológicamente (más recientes primero)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, d.name as doctor_name, s.name as specialty_name
            FROM medical_formulas f
            JOIN doctors d ON f.doctor_id = d.id
            JOIN specialties s ON d.specialty_id = s.id
            WHERE f.patient_id = ?
            ORDER BY f.issue_date DESC, f.id DESC;
        """, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]


# =====================================================================
# OPERACIONES CRUD - EXÁMENES MÉDICOS (MEDICAL EXAMS)
# =====================================================================

def create_exam(patient_id, exam_name, upload_date, file_path, notes=""):
    """Registra la carga de un resultado de examen en formato PDF."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medical_exams (patient_id, exam_name, upload_date, file_path, notes)
            VALUES (?, ?, ?, ?, ?);
        """, (patient_id, exam_name, upload_date, file_path, notes))
        conn.commit()
        return cursor.lastrowid

def get_exams_by_patient(patient_id):
    """Retorna la lista de exámenes clínicos subidos por el paciente ordenados cronológicamente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM medical_exams 
            WHERE patient_id = ?
            ORDER BY upload_date DESC;
        """, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_exam(exam_id, patient_id):
    """Elimina el registro de un examen si pertenece al paciente indicado."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Primero obtenemos el path del archivo físico
        cursor.execute("SELECT file_path FROM medical_exams WHERE id = ? AND patient_id = ?;", (exam_id, patient_id))
        row = cursor.fetchone()
        if row:
            file_path = row["file_path"]
            # Borrar el registro de la BD
            cursor.execute("DELETE FROM medical_exams WHERE id = ? AND patient_id = ?;", (exam_id, patient_id))
            conn.commit()
            return file_path
        return None
