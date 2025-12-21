document.addEventListener('DOMContentLoaded', () => {
    console.log('Portafolio interactivo cargado.');

    // --- Scroll Suave (Smooth Scrolling) ---
    const navLinks = document.querySelectorAll('nav a[href^="#"]');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // --- Resaltado de Enlace Activo al Navegar ---
    const sections = document.querySelectorAll('main section[id]');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const id = entry.target.getAttribute('id');
            const correspondingLink = document.querySelector(`nav a[href="#${id}"]`);

            if (entry.isIntersecting) {
                correspondingLink.classList.add('active');
            } else {
                correspondingLink.classList.remove('active');
            }
        });
    }, { rootMargin: "-50% 0px -50% 0px" }); // Activa el enlace cuando la sección está en el centro de la pantalla

    sections.forEach(section => observer.observe(section));

    // --- Manejo del Formulario de Contacto ---
    const formulario = document.querySelector('.formulario-contacto');
    
    if (formulario) {
        const estadoMensaje = document.getElementById('estado-mensaje');
        const botonEnviar = formulario.querySelector('button[type="submit"]');

        formulario.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const datos = {
                nombre: document.getElementById('nombre').value,
                email: document.getElementById('email').value,
                mensaje: document.getElementById('mensaje').value
            };
            
            // Limpiar estado previo
            const textoOriginalBoton = botonEnviar.textContent;
            botonEnviar.disabled = true;
            botonEnviar.textContent = 'Enviando...';
            if (estadoMensaje) estadoMensaje.style.display = 'none';

            try {
                const respuesta = await fetch('http://127.0.0.1:8000/api/contacto', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datos)
                });

                if (respuesta.ok) {
                    formulario.reset();
                    if (estadoMensaje) {
                        estadoMensaje.textContent = '¡Mensaje enviado con éxito!';
                        estadoMensaje.style.color = '#28a745'; // Verde
                        estadoMensaje.style.display = 'block';
                    } else {
                        alert('¡Mensaje enviado con éxito!');
                    }
                } else {
                    throw new Error('Error en el envío');
                }
            } catch (error) {
                console.error('Error:', error);
                if (estadoMensaje) {
                    estadoMensaje.textContent = 'Hubo un error al enviar el mensaje.';
                    estadoMensaje.style.color = '#dc3545'; // Rojo
                    estadoMensaje.style.display = 'block';
                } else {
                    alert('Error de conexión con el servidor.');
                }
            } finally {
                // Restaurar el estado del botón
                botonEnviar.disabled = false;
                botonEnviar.textContent = textoOriginalBoton;

                // Ocultar el mensaje de estado después de 5 segundos
                setTimeout(() => {
                    if (estadoMensaje) estadoMensaje.style.display = 'none';
                }, 5000);
            }
        });
    }
});