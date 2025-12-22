import os
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select

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
# Cambiamos el nombre para forzar la creación de una nueva DB y evitar errores de columnas faltantes
sqlite_file_name = "portafolio.db"
base_dir = os.path.dirname(os.path.abspath(__file__))
sqlite_url = f"sqlite:///{os.path.join(base_dir, sqlite_file_name)}"
# 'echo=True' es útil para ver las sentencias SQL que se ejecutan en la terminal.
engine = create_engine(sqlite_url, echo=True)

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

# 5. Actualizar el endpoint para que guarde en la base de datos
@app.post("/api/contacto")
def recibir_contacto(contacto: Contacto):
    with Session(engine) as session:
        session.add(contacto)
        session.commit()
        session.refresh(contacto)

    print(f"Guardado en DB: {contacto}")
    return {"mensaje": "Mensaje recibido y guardado exitosamente"}

# 6. Leer todos los contactos (Read All)
@app.get("/api/contactos", response_model=list[Contacto])
def leer_contactos():
    with Session(engine) as session:
        contactos = session.exec(select(Contacto)).all()
        return contactos

# 7. Leer un contacto por ID (Read One)
@app.get("/api/contacto/{contacto_id}", response_model=Contacto)
def leer_contacto(contacto_id: int):
    with Session(engine) as session:
        contacto = session.get(Contacto, contacto_id)
        if not contacto:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        return contacto

# 8. Actualizar un contacto (Update)
@app.put("/api/contacto/{contacto_id}", response_model=Contacto)
def actualizar_contacto(contacto_id: int, contacto_actualizado: Contacto):
    with Session(engine) as session:
        contacto_db = session.get(Contacto, contacto_id)
        if not contacto_db:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        contacto_db.nombre = contacto_actualizado.nombre
        contacto_db.email = contacto_actualizado.email
        contacto_db.mensaje = contacto_actualizado.mensaje
        
        session.add(contacto_db)
        session.commit()
        session.refresh(contacto_db)
        return contacto_db

# 9. Eliminar un contacto (Delete)
@app.delete("/api/contacto/{contacto_id}")
def eliminar_contacto(contacto_id: int):
    with Session(engine) as session:
        contacto = session.get(Contacto, contacto_id)
        if not contacto:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        session.delete(contacto)
        session.commit()
        return {"mensaje": "Contacto eliminado exitosamente"}