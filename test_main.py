import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from main import app, get_session, Contacto, get_current_user, limiter

# 1. Configuración de Base de Datos de Prueba (En memoria)
# Usamos StaticPool para que la DB en memoria funcione con múltiples hilos si es necesario
engine_test = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

# Desactivar el Rate Limiter durante las pruebas para evitar falsos positivos
limiter.enabled = False

# 2. Fixture: Prepara la base de datos antes de cada test y la limpia después
@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine_test)
    with Session(engine_test) as session:
        yield session
    SQLModel.metadata.drop_all(engine_test)

# 3. Fixture: Cliente de prueba con la dependencia de DB sobrescrita
@pytest.fixture(name="client")
def client_fixture(session: Session):
    # Función para reemplazar get_session en main.py
    def get_session_override():
        return session

    # Override auth: Simulamos que siempre hay un usuario logueado ("admin")
    def get_current_user_override():
        return "admin"

    # Sobrescribimos la dependencia
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    
    client = TestClient(app)
    yield client
    
    # Limpiamos la sobrescritura después del test
    app.dependency_overrides.clear()

# 4. Prueba: Crear un contacto (POST)
def test_crear_contacto(client: TestClient, monkeypatch):
    # Mockear (simular) el envío de correo para que no intente enviar uno real
    monkeypatch.setattr("main.enviar_notificacion_admin", lambda *args: None)

    payload = {
        "nombre": "Usuario Test",
        "email": "test@ejemplo.com",
        "mensaje": "Este es un mensaje de prueba automatizada"
    }
    
    response = client.post("/api/contacto", json=payload)
    
    data = response.json()
    
    assert response.status_code == 200
    assert data["nombre"] == "Usuario Test"
    assert data["email"] == "test@ejemplo.com"
    assert "id" in data

# 5. Prueba: Leer contactos (GET)
def test_leer_contactos(client: TestClient):
    response = client.get("/api/contactos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# 6. Prueba: Actualizar un contacto (PUT)
def test_actualizar_contacto(client: TestClient, monkeypatch):
    # 1. Crear un contacto primero para tener algo que editar
    monkeypatch.setattr("main.enviar_notificacion_admin", lambda *args: None)
    res_crear = client.post("/api/contacto", json={
        "nombre": "Original", "email": "orig@test.com", "mensaje": "Original"
    })
    contacto_id = res_crear.json()["id"]

    # 2. Actualizarlo
    payload = {"nombre": "Editado", "email": "edit@test.com", "mensaje": "Editado"}
    res_update = client.put(f"/api/contacto/{contacto_id}", json=payload)
    
    assert res_update.status_code == 200
    assert res_update.json()["nombre"] == "Editado"

# 7. Prueba: Eliminar un contacto (DELETE)
def test_eliminar_contacto(client: TestClient, monkeypatch):
    # 1. Crear un contacto primero
    monkeypatch.setattr("main.enviar_notificacion_admin", lambda *args: None)
    res_crear = client.post("/api/contacto", json={
        "nombre": "Borrar", "email": "borrar@test.com", "mensaje": "Adios"
    })
    contacto_id = res_crear.json()["id"]

    # 2. Eliminarlo
    res_delete = client.delete(f"/api/contacto/{contacto_id}")
    assert res_delete.status_code == 200
    
    # 3. Verificar que ya no existe (debe dar error 404)
    res_get = client.get(f"/api/contacto/{contacto_id}")
    assert res_get.status_code == 404