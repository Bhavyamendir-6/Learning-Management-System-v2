# Quick Start Guide

Welcome to the LMS Agent UI! This application consists of a **FastAPI backend** and a **Next.js frontend**. You must run both servers simultaneously to use the application.

## 🚀 Prerequisites

Before starting, ensure you have:
1. Python 3.10+ installed
2. Node.js 18+ installed
3. A configured `.env` file in the project root (`LMS_Project/.env`) containing:
   ```env
   GEMINI_API_KEY=your_gemini_key
   POSTGRES_URL=your_postgres_connection_string
   JWT_SECRET_KEY=your_jwt_secret
   ```
   - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Get a free PostgreSQL database from [Neon](https://neon.tech)
   - Generate a JWT secret: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## Step 1: Install Dependencies

Open a terminal in the root directory (`LMS_Project`) and run:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Mac/Linux
# .venv\Scripts\activate   # On Windows

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd nextjs_frontend
npm install
cd ..
```

---

## Step 2: Start the Backend (FastAPI)

Open a terminal in the root directory (`LMS_Project`) and run:

```bash
# 1. Activate the virtual environment
source .venv/bin/activate  # On Mac/Linux
# .venv\Scripts\activate   # On Windows

# 2. Start the FastAPI server
python -m fastapi_backend.app
```
*The backend will start on `http://localhost:5001`.*

---

## Step 3: Start the Frontend (Next.js)

Open **a new, second terminal window** and run:

```bash
# 1. Navigate into the Next.js frontend folder
cd nextjs_frontend

# 2. Start the Next.js development server
npm run dev
```

> **Note:** If you run `npm run dev` in the root directory, you will get a `Missing script: "dev"` error. You **must** be inside the `nextjs_frontend` folder.

---

## Step 4: Access the Application

Once both servers are running, open your web browser and navigate to:

👉 **[http://localhost:3000](http://localhost:3000)**

You can now sign up, log in, upload PDF documents, and interact with the AI assistant!

---

## 💡 Tips

- The database schema is bootstrapped automatically on first startup — no manual SQL required.
- Use the **Quick Action Buttons** in the sidebar for common tasks like generating quizzes, summaries, and flashcards.
- Check out the **Community Hub** to explore quizzes and flashcards shared by others, and compete on the **Leaderboard**!
- Toggle between **dark** and **light** themes using the theme button in the UI.
- The sidebar is **resizable** — drag its edge to adjust width.
