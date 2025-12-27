import CONFIG from './config.js';

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('#login-form form');
    const signupForm = document.querySelector('#signup-form form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                    credentials: 'include'
                });
                const result = await response.json();
                if (result.success) {
                    window.location.href = result.redirect;
                } else {
                    alert(result.message);
                }
            } catch (err) {
                console.error("Login Error", err);
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(signupForm);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                    credentials: 'include'
                });
                const result = await response.json();
                if (result.success) {
                    window.location.href = result.redirect;
                } else {
                    alert(result.message);
                }
            } catch (err) {
                console.error("Signup Error", err);
            }
        });
    }
});
