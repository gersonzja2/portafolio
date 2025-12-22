import os
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import EmailStr
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cargar variables de entorno desde el archivo .env al inicio
load_dotenv()

# 1. Definir el modelo de la base de datos con SQLModel
# Concepto: DTOs (Data Transfer Objects). Creamos una clase base para los campos comunes.
class ContactoBase(SQLModel):
    nombre: str
    email: EmailStr
    mensaje: str

# Modelo para la tabla de la base de datos (hereda de Base)
class Contacto(ContactoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creado_en: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

# Modelo para recibir datos (Create) - El usuario solo envía estos datos
class ContactoCreate(ContactoBase):
    pass

# Modelo para devolver datos (Read) - Incluye ID y fecha
class ContactoRead(ContactoBase):
    id: int
    creado_en: datetime

# 2. Crear el motor de la base de datos
# Usaremos SQLite, que es una base de datos en un solo archivo.
# Cambiamos el nombre para forzar la creación de una nueva DB y evitar errores de columnas faltantes
sqlite_file_name = "portafolio.db"
base_dir = os.path.dirname(os.path.abspath(__file__))
default_db_url = f"sqlite:///{os.path.join(base_dir, sqlite_file_name)}"
# Concepto: Variables de Entorno. Usamos la URL del .env o la por defecto.
sqlite_url = os.getenv("DATABASE_URL", default_db_url)
# 'echo=True' es útil para ver las sentencias SQL que se ejecutan en la terminal.
engine = create_engine(sqlite_url, echo=True)

# Configuración de Email (SMTP)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def enviar_correo_respuesta(email_destino: str, nombre: str):
    """Envía un correo de confirmación en segundo plano."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("⚠️ Credenciales SMTP no configuradas. No se envió el correo.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email_destino
        msg['Subject'] = "Gracias por contactarme"

        cuerpo = f"Hola {nombre},\n\nGracias por visitar mi portafolio. He recibido tu mensaje correctamente y te responderé a la brevedad.\n\nSaludos."
        msg.attach(MIMEText(cuerpo, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Correo enviado a {email_destino}")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")

# 3. Función para crear la tabla en la base de datos si no existe
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 4. Ciclo de vida de la aplicación (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Configurar CORS (esto ya lo tenías)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, cambia esto por tu dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Concepto: Inyección de Dependencias. Función para obtener la sesión de DB.
def get_session():
    with Session(engine) as session:
        yield session

# 5. Actualizar el endpoint para que guarde en la base de datos
@app.post("/api/contacto", response_model=ContactoRead)
def recibir_contacto(contacto: ContactoCreate, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    # Convertimos el modelo de entrada (Create) al modelo de base de datos (Table)
    contacto_db = Contacto.model_validate(contacto)
    session.add(contacto_db)
    session.commit()
    session.refresh(contacto_db)
    
    # Enviar correo en segundo plano (no bloquea la respuesta al usuario)
    background_tasks.add_task(enviar_correo_respuesta, contacto.email, contacto.nombre)
    
    print(f"Guardado en DB: {contacto_db}")
    return contacto_db

# 6. Leer todos los contactos (Read All)
@app.get("/api/contactos", response_model=list[ContactoRead])
def leer_contactos(session: Session = Depends(get_session)):
    contactos = session.exec(select(Contacto)).all()
    return contactos

# 7. Leer un contacto por ID (Read One)
@app.get("/api/contacto/{contacto_id}", response_model=ContactoRead)
def leer_contacto(contacto_id: int, session: Session = Depends(get_session)):
    contacto = session.get(Contacto, contacto_id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contacto

# 8. Actualizar un contacto (Update)
@app.put("/api/contacto/{contacto_id}", response_model=ContactoRead)
def actualizar_contacto(contacto_id: int, contacto_actualizado: ContactoCreate, session: Session = Depends(get_session)):
    contacto_db = session.get(Contacto, contacto_id)
    if not contacto_db:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    # Actualizamos los campos usando el modelo base
    contacto_db.sqlmodel_update(contacto_actualizado)
    
    session.add(contacto_db)
    session.commit()
    session.refresh(contacto_db)
    return contacto_db

# 9. Eliminar un contacto (Delete)
@app.delete("/api/contacto/{contacto_id}")
def eliminar_contacto(contacto_id: int, session: Session = Depends(get_session)):
    contacto = session.get(Contacto, contacto_id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    session.delete(contacto)
    session.commit()
    return {"mensaje": "Contacto eliminado exitosamente"}