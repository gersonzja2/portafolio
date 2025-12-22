const API_URL = 'https://portafolio-backend-6efq.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    
    // Si hay token guardado, intentamos mostrar el dashboard directamente
    if (token) {
        mostrarDashboard();
    } else {
        mostrarLogin();
    }

    // Botón de Cerrar Sesión
    document.getElementById('btn-logout').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });

    // Formulario de Login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('error-login');

            // FastAPI espera los datos como formulario (x-www-form-urlencoded), no como JSON
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const res = await fetch(`${API_URL}/token`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });

                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('token', data.access_token); // Guardar token
                    mostrarDashboard();
                    loginForm.reset();
                    errorMsg.style.display = 'none';
                } else {
                    errorMsg.textContent = 'Usuario o contraseña incorrectos';
                    errorMsg.style.display = 'block';
                }
            } catch (error) {
                errorMsg.textContent = 'Error de conexión con el servidor';
                errorMsg.style.display = 'block';
            }
        });
    }
});

function mostrarLogin() {
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('btn-logout').style.display = 'none';
}

function mostrarDashboard() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('dashboard-section').style.display = 'block';
    document.getElementById('btn-logout').style.display = 'inline';
    cargarMensajes();
}

function logout() {
    localStorage.removeItem('token');
    mostrarLogin();
}

async function cargarMensajes() {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`${API_URL}/api/contactos`, {
            headers: { 'Authorization': `Bearer ${token}` } // Enviamos el token aquí
        });

        if (res.status === 401) {
            // Si el token venció o es inválido
            logout();
            return;
        }

        const mensajes = await res.json();
        const tbody = document.querySelector('#tabla-mensajes tbody');
        tbody.innerHTML = '';

        mensajes.forEach(msg => {
            const tr = document.createElement('tr');
            const fecha = new Date(msg.creado_en).toLocaleString();
            tr.innerHTML = `
                <td>${fecha}</td>
                <td>${msg.nombre}</td>
                <td>${msg.email}</td>
                <td>${msg.mensaje}</td>
                <td>
                    <button onclick="eliminarMensaje(${msg.id})" style="background: #e74c3c; padding: 5px 10px; font-size: 0.9rem;">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error cargando mensajes', error);
    }
}

// Función global para poder llamarla desde el HTML generado dinámicamente
window.eliminarMensaje = async (id) => {
    if (!confirm('¿Estás seguro de eliminar este mensaje?')) return;
    
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`${API_URL}/api/contacto/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
            cargarMensajes(); // Recargar la tabla
        } else {
            alert('Error al eliminar el mensaje');
        }
    } catch (error) {
        console.error(error);
    }
};