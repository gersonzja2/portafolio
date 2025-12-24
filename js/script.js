const API_URL = 'https://portafolio-backend-6efq.onrender.com'; // Cambiar por tu URL de Render al desplegar
const GITHUB_USERNAME = 'gersonzja2'; // TU USUARIO DE GITHUB

document.addEventListener('DOMContentLoaded', () => {
    const formulario = document.querySelector('.formulario-contacto');
    const estadoMensaje = document.getElementById('estado-mensaje');

    // --- Lógica del Modo Oscuro ---
    const btnTema = document.getElementById('btn-tema');
    const body = document.body;

    // 1. Cargar preferencia guardada
    if (localStorage.getItem('tema') === 'oscuro') {
        body.classList.add('dark-mode');
        if (btnTema) btnTema.textContent = '☀️';
    }

    // 2. Alternar tema al hacer clic
    if (btnTema) {
        btnTema.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const esOscuro = body.classList.contains('dark-mode');
            
            // Guardar en localStorage y cambiar icono
            localStorage.setItem('tema', esOscuro ? 'oscuro' : 'claro');
            btnTema.textContent = esOscuro ? '☀️' : '🌙';
        });
    }

    // --- Animación Scroll Reveal ---
    const observerOptions = {
        threshold: 0.15 // Se activa cuando el 15% del elemento es visible
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Dejar de observar para que no se repita
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal').forEach(section => {
        observer.observe(section);
    });

    cargarRepositorios();

    if (formulario) {
        formulario.addEventListener('submit', async (event) => {
            event.preventDefault(); // Evitar que la página se recargue

            // 1. Mostrar estado de "Enviando..." y bloquear botón
            const botonSubmit = formulario.querySelector('button[type="submit"]');
            const textoOriginal = botonSubmit.textContent;
            botonSubmit.disabled = true;
            botonSubmit.textContent = 'Enviando...';
            
            estadoMensaje.style.display = 'block';
            estadoMensaje.style.color = '#333';
            estadoMensaje.textContent = 'Procesando tu solicitud...';

            // 2. Capturar los datos del formulario
            const datos = {
                nombre: document.getElementById('nombre').value,
                email: document.getElementById('email').value,
                mensaje: document.getElementById('mensaje').value
            };

            try {
                // 3. Enviar los datos al backend (API)
                // Nota: Asegúrate de que tu servidor (uvicorn) esté corriendo en el puerto 8000
                const respuesta = await fetch(`${API_URL}/api/contacto`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(datos)
                });

                // 4. Manejar la respuesta
                if (respuesta.ok) {
                    estadoMensaje.style.color = 'green';
                    estadoMensaje.textContent = '¡Mensaje enviado con éxito! Gracias por contactarme.';
                    formulario.reset(); // Limpiar los campos
                } else {
                    // Si hay error (ej. email inválido), mostramos el detalle
                    const errorData = await respuesta.json();
                    // A veces el error viene en una lista 'detail' (formato de FastAPI)
                    const mensajeError = Array.isArray(errorData.detail) 
                        ? errorData.detail[0].msg 
                        : (errorData.detail || 'No se pudo enviar el mensaje.');
                    
                    estadoMensaje.style.color = 'red';
                    estadoMensaje.textContent = 'Error: ' + mensajeError;
                }
            } catch (error) {
                console.error('Error de conexión:', error);
                estadoMensaje.style.color = 'red';
                estadoMensaje.textContent = 'Error de conexión. Asegúrate de que el servidor esté encendido.';
            } finally {
                // 5. Restaurar el botón
                botonSubmit.disabled = false;
                botonSubmit.textContent = textoOriginal;
                
                // Ocultar mensaje de éxito después de 5 segundos
                if (estadoMensaje.style.color === 'green') {
                    setTimeout(() => {
                        estadoMensaje.style.display = 'none';
                    }, 5000);
                }
            }
        });
    }
});

async function cargarRepositorios() {
    const contenedor = document.getElementById('contenedor-proyectos');
    if (!contenedor) return;

    try {
        // Fetch a la API de GitHub: ordenados por actualización, máximo 6 repositorios
        const respuesta = await fetch(`https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=6`);
        
        if (!respuesta.ok) throw new Error('Error al obtener repositorios');
        
        const repos = await respuesta.json();
        contenedor.innerHTML = ''; // Limpiar mensaje de carga

        repos.forEach(repo => {
            const div = document.createElement('div');
            div.classList.add('proyecto'); // Reutilizamos tu clase CSS existente
            div.innerHTML = `
                <h3>${repo.name}</h3>
                <p>${repo.description ? repo.description : 'Sin descripción disponible.'}</p>
                <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer" style="display:inline-block; margin-top:10px; font-weight:bold;">Ver en GitHub</a>
            `;
            contenedor.appendChild(div);
        });
    } catch (error) {
        console.error('Error cargando GitHub:', error);
        contenedor.innerHTML = '<p>No se pudieron cargar los proyectos en este momento.</p>';
    }
}