import os
import socket
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import EmailStr
from dotenv import load_dotenv
import smtplib
from jose import JWTError, jwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Cargar variables de entorno desde el archivo .env al inicio
load_dotenv()

# Parche para forzar IPv4 (Solución para [Errno 101] Network is unreachable)
# Render y otros servicios a veces intentan usar IPv6 por defecto y fallan con Gmail.
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

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
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Verificación rápida al iniciar para depuración
if not SMTP_USERNAME or not SMTP_PASSWORD:
    print("\n⚠️  ADVERTENCIA: No se detectaron credenciales SMTP en el archivo .env")
    print("   El envío de correos no funcionará hasta que reinicies el servidor o corrijas el archivo.\n")

def enviar_correo_respuesta(email_destino: str, nombre: str):
    """Envía un correo de confirmación en segundo plano."""
    print(f"📧 Iniciando intento de envío de correo a {email_destino}...")
    print(f"🔌 Puerto SMTP en uso: {SMTP_PORT}")
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

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Correo enviado a {email_destino}")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")

# Configuración de Seguridad (JWT)
SECRET_KEY = os.getenv("SECRET_KEY", "supersecreto_cambiar_en_produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(SQLModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != ADMIN_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# 3. Función para crear la tabla en la base de datos si no existe
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 4. Ciclo de vida de la aplicación (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# Configuración de Rate Limiting (Anti-Spam)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)

# Configurar CORS (esto ya lo tenías)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, cambia esto por tu dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint raíz para verificar que la API está en línea (Health Check)
@app.get("/")
def root():
    return {"mensaje": "API del Portafolio funcionando correctamente"}

# Agregar el manejador de excepciones de Rate Limit a la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Concepto: Inyección de Dependencias. Función para obtener la sesión de DB.
def get_session():
    with Session(engine) as session:
        yield session

# Endpoint para Login (Obtener Token)
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != ADMIN_USERNAME or form_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 5. Actualizar el endpoint para que guarde en la base de datos
@app.post("/api/contacto", response_model=ContactoRead)
@limiter.limit("5/minute") # Límite: 5 mensajes por minuto por IP
def recibir_contacto(request: Request, contacto: ContactoCreate, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
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
def leer_contactos(session: Session = Depends(get_session), current_user: str = Depends(get_current_user)):
    contactos = session.exec(select(Contacto)).all()
    return contactos

# 7. Leer un contacto por ID (Read One)
@app.get("/api/contacto/{contacto_id}", response_model=ContactoRead)
def leer_contacto(contacto_id: int, session: Session = Depends(get_session), current_user: str = Depends(get_current_user)):
    contacto = session.get(Contacto, contacto_id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contacto

# 8. Actualizar un contacto (Update)
@app.put("/api/contacto/{contacto_id}", response_model=ContactoRead)
def actualizar_contacto(contacto_id: int, contacto_actualizado: ContactoCreate, session: Session = Depends(get_session), current_user: str = Depends(get_current_user)):
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
def eliminar_contacto(contacto_id: int, session: Session = Depends(get_session), current_user: str = Depends(get_current_user)):
    contacto = session.get(Contacto, contacto_id)
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    session.delete(contacto)
    session.commit()
    return {"mensaje": "Contacto eliminado exitosamente"}