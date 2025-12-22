document.addEventListener('DOMContentLoaded', () => {
    const formulario = document.querySelector('.formulario-contacto');
    const estadoMensaje = document.getElementById('estado-mensaje');

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
                const respuesta = await fetch('http://127.0.0.1:8000/api/contacto', {
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