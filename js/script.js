const API_URL = 'https://portafolio-backend-6efq.onrender.com'; // Cambiar por tu URL de Render al desplegar

// 1. Log global para confirmar que el archivo JS se cargó (Evitar problemas de caché)
console.log("✅ script.js cargado correctamente. API:", API_URL);

document.addEventListener('DOMContentLoaded', () => {
    const formulario = document.querySelector('.formulario-contacto');
    const estadoMensaje = document.getElementById('estado-mensaje');

    if (formulario) {
        console.log("✅ Formulario encontrado. Listener activado.");
        formulario.addEventListener('submit', async (event) => {
            event.preventDefault(); // Evitar que la página se recargue
            console.log("✅ Botón enviar presionado.");

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

            console.log("🚀 Iniciando envío a:", `${API_URL}/api/contacto`);
            console.log("📦 Datos capturados:", datos);

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

                console.log("📡 Respuesta del servidor (Status):", respuesta.status);

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
                console.error('❌ Error de conexión (Catch):', error);
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