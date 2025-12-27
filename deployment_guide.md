# Decoupled Deployment Guide: Render & Vercel 🚀☁️

This guide outlines how to host your backend on **Render** (as an API) and your frontend on **Vercel** (as a static site).

## 🏗️ Architecture Overview
- **Backend (Render)**: Processes logic, AI generation, and database interactions.
- **Frontend (Vercel)**: Serves the HTML, CSS, and JavaScript. Communicates with Render via `fetch()`.

---

## 🟢 Part 1: Deploy Backend (Render)

1.  **Log in to Render** and click **New > Web Service**.
2.  **Connect your GitHub Repository**: `Ai-in-gaming`.
3.  **Configure Settings**:
    -   **Name**: `ai-gaming-backend`
    -   **Environment**: `Python 3`
    -   **Region**: (Choose closest to you)
    -   **Build Command**: `pip install -r backend/requirements.txt`
    -   **Start Command**: `gunicorn --chdir backend app:app`
4.  **Environment Variables**:
    -   `DATABASE_URL`: Your Supabase connection string.
    -   `GROQ_API_KEY`: Your Groq API key.
    -   `SECRET_KEY`: A long random string.
5.  **Wait for Deployment**: Once "Live", copy your backend URL (e.g., `https://ai-gaming-backend.onrender.com`).

---

## 🔵 Part 2: Configure Frontend API Discovery

Before deploying to Vercel, you must point the frontend to your Render URL.

1.  Open `frontend/static/js/config.js`.
2.  Update the `API_BASE_URL`:
    ```javascript
    const CONFIG = {
        API_BASE_URL: "https://your-render-app-url.onrender.com" // REPLACE THIS
    };
    ```
3.  **Commit and Push** this change to GitHub.

---

## 🟡 Part 3: Deploy Frontend (Vercel)

1.  **Log in to Vercel** and click **Add New > Project**.
2.  **Import your GitHub Repository**: `Ai-in-gaming`.
3.  **Project Settings**:
    -   **Framework Preset**: `Other` (or `Vite/React` if prompted, but `Other` is fine for static).
    -   **Root Directory**: Click "Edit" and select the `frontend` folder.
4.  **Click Deploy**.
5.  Vercel will provide a URL (e.g., `https://ai-gaming-frontend.vercel.app`).

---

## 🔒 Security Note: CORS
The backend is configured to accept requests with credentials. Ensure your `SECRET_KEY` is consistent. If you face "CORS" errors, double-check that `config.js` has the EXACT Render URL (no trailing slash).

---

## ✅ Verification
1.  Visit your Vercel URL.
2.  Try to Sign Up.
3.  If successful, you will be redirected to the Persona page, confirming the Frontend-Backend bridge is active!
