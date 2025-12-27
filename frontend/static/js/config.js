// API Configuration for Decoupled Frontend
const CONFIG = {
    // Replace with your Render backend URL once deployed, e.g., "https://ai-gaming-backend.onrender.com"
    API_BASE_URL: window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
        ? "http://127.0.0.1:5000"
        : "https://your-render-app-url.onrender.com"
};

export default CONFIG;
