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
    -   **Start Command**: `gunicorn --chdir backend app:app` (IMPORTANT: Ensure this is set correctly in settings)
4.  **Environment Variables**:
    -   `DATABASE_URL`: Your Supabase connection string.
        > [!IMPORTANT]
        > If your password contains special characters like `@`, `#`, or `:`, you **MUST** URL-encode it (e.g., `@` becomes `%40`). Visit [urlencoder.org](https://www.urlencoder.org/) to encode your password.
    -   `GROQ_API_KEY`: Your Groq API key.
    -   `SECRET_KEY`: A long random string.
    -   `FRONTEND_URL`: Your Vercel URL (e.g., `https://ai-gaming-frontend.vercel.app`)
5.  **Wait for Deployment**: Once "Live", copy your backend URL (e.g., `https://ai-gaming-backend.onrender.com`).
6.  **Verify Backend Health**: Visit `https://your-backend-url.onrender.com/api/health`. You should see `{"status": "healthy"}`. If you see an error, check Render "Logs".

> [!WARNING]
> If you see an error like `ModuleNotFoundError: No module named 'your_application'`, it means Render is using its default start command. Go to your **Web Service Settings > General** and manually change the **Start Command** to `gunicorn --chdir backend app:app`.

---

## 🔵 Part 2: Configure Frontend Environment

The frontend uses **Vite** for native environment support. **Do not hardcode URLs.**

1.  Open your **Vercel Dashboard**.
2.  Go to **Settings > Environment Variables**.
3.  Add a new variable:
    -   **Key**: `VITE_BACKEND_URL` (Wait! It must start with `VITE_`)
    -   **Value**: `https://ai-gaming-backend.onrender.com` (Your Render URL)

---

## 🟡 Part 3: Deploy Frontend (Vercel)

1.  **Project Settings**:
    -   **Framework Preset**: `Vite` (Vercel will detect the `package.json` and `vite.config.js`)
    -   **Root Directory**: `frontend`
2.  **Build & Development Settings**:
    -   Vercel will automatically set the build command to `npm run build` and the output directory to `dist`.
3.  **Click Deploy**. Vercel will build the project and bake your `VITE_BACKEND_URL` into the production assets.

> [!TIP]
> Vite handles multi-page application (MPA) support via the `vite.config.js` I've created. All your `.html` files will be bundled into the `dist` folder.

---

## 🔒 Security Note: CORS
The backend is configured to accept requests with credentials. Ensure your `SECRET_KEY` is consistent. If you face "CORS" errors, double-check that `config.js` has the EXACT Render URL (no trailing slash).

---

## ✅ Verification
1.  Visit your Vercel URL.
2.  Check the browser console (F12). You should no longer see `favicon.ico` or `__BACKEND_URL__` errors.
3.  Try to Sign Up. If it works, the system is fully healthy!

> [!IMPORTANT]
> If you just added or changed an **Environment Variable** on Vercel, you **must** redeploy for it to take effect. Go to the "Deployments" tab, click the three dots `...` on the latest build, and select **Redeploy**.
