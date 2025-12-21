from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS para permitir peticiones desde tu página web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, cambia esto por tu dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Contacto(BaseModel):
    nombre: str
    email: str
    mensaje: str

@app.post("/api/contacto")
async def recibir_contacto(contacto: Contacto):
    print(f"Nuevo mensaje de {contacto.nombre} ({contacto.email}): {contacto.mensaje}")
    return {"mensaje": "Correo recibido exitosamente"}