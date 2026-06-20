// Hamburger menu
const hamburger = document.getElementById('hamburger');
const nav = document.querySelector('nav');
if (hamburger && nav) {
    hamburger.addEventListener('click', () => nav.classList.toggle('nav-open'));
    nav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => nav.classList.remove('nav-open'));
    });
}

// Password visibility toggle
const passwordToggle = document.getElementById('password-toggle');
if (passwordToggle) {
    const passwordInput = document.getElementById('password');
    const icon = passwordToggle.querySelector('i');
    passwordToggle.addEventListener('click', (e) => {
        e.preventDefault();
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        icon.className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
    });
}

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('SW registered'))
            .catch(err => console.log('SW failed:', err));
    });
}
