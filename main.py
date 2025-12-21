import os
from typing import Optional
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine

# 1. Definir el modelo de la base de datos con SQLModel
# SQLModel combina Pydantic y SQLAlchemy. 'table=True' lo convierte en una tabla de base de datos.
class Contacto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.utcnow, nullable=False)
    nombre: str
    email: str
    mensaje: str

# 2. Crear el motor de la base de datos
# Usaremos SQLite, que es una base de datos en un solo archivo.
sqlite_file_name = "database.db"
base_dir = os.path.dirname(os.path.abspath(__file__))
sqlite_url = f"sqlite:///{os.path.join(base_dir, sqlite_file_name)}"
# 'echo=True' es útil para ver las sentencias SQL que se ejecutan en la terminal.
engine = create_engine(sqlite_url, echo=True)

# 3. Función para crear la tabla en la base de datos si no existe
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

# 4. Evento de inicio: se ejecuta una vez cuando FastAPI arranca.
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Configurar CORS (esto ya lo tenías)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, cambia esto por tu dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Actualizar el endpoint para que guarde en la base de datos
@app.post("/api/contacto")
async def recibir_contacto(contacto: Contacto):
    with Session(engine) as session:
        session.add(contacto)
        session.commit()
        session.refresh(contacto)

    print(f"Guardado en DB: {contacto}")
    return {"mensaje": "Mensaje recibido y guardado exitosamente"}