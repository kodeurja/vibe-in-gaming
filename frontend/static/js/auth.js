import CONFIG from './config.js';

const Auth = {
    async checkStatus() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/user_status`, {
                credentials: 'include'
            });
            return await response.json();
        } catch (err) {
            console.error("Auth check failed", err);
            return { authenticated: false };
        }
    },

    async logout() {
        try {
            await fetch(`${CONFIG.API_BASE_URL}/logout`, {
                credentials: 'include'
            });
            window.location.href = 'index.html';
        } catch (err) {
            console.error("Logout failed", err);
        }
    }
};

// Initialize navigation and status
document.addEventListener('DOMContentLoaded', async () => {
    const status = await Auth.checkStatus();
    const navbar = document.getElementById('navbar');
    const logoutBtn = document.getElementById('logout-btn');

    if (status.authenticated) {
        if (navbar) navbar.style.display = 'flex';
        if (logoutBtn) {
            logoutBtn.onclick = (e) => {
                e.preventDefault();
                Auth.logout();
            }
        }
    } else {
        // Redirect to index if on a protected page
        const protectedPages = ['hub.html', 'roadmap.html', 'game_dashboard.html', 'persona.html', 'quiz.html', 'puzzle.html'];
        const currentPage = window.location.pathname.split('/').pop();
        if (protectedPages.includes(currentPage)) {
            window.location.href = 'index.html';
        }
    }
});

export default Auth;
