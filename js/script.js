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
});