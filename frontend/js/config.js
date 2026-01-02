const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
let apiBase = import.meta.env.VITE_BACKEND_URL;

// Safety check: specific override for Vercel if environment variable is accidentally set to localhost
if (apiBase && !isLocal && (apiBase.includes('localhost') || apiBase.includes('127.0.0.1'))) {
    console.warn('Ignoring localhost API URL in production');
    apiBase = "";
}

const CONFIG = {
    API_BASE_URL: (isLocal ? (apiBase || "http://localhost:5000") : (apiBase || ""))
};

export default CONFIG;
