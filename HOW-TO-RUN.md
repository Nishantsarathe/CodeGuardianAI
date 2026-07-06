# 🚀 HOW TO RUN — CodeGuardian AI

Complete step-by-step guide to install, configure and run the project from a fresh download.

---

## 📋 Prerequisites

You need three things installed before you start:

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.11 or newer | https://www.python.org/downloads |
| Node.js | 20 or newer | https://nodejs.org |
| Ollama | Latest | https://ollama.com/download |

To check what you have, open a terminal and run:
```
python --version
node --version
ollama --version
```

---

## ⚡ OPTION A — Run Locally (Recommended for first time)

### Step 1 — Extract the project

Unzip the downloaded file. You will get a folder called `codeguardian-ai-fixed`.  
Open a terminal inside that folder.

**Windows (PowerShell or Command Prompt):**
```
cd codeguardian-ai-fixed
```

**Mac / Linux:**
```
cd codeguardian-ai-fixed
```

---

### Step 2 — Pull the AI model

This downloads the AI brain that powers all 10 agents.  
Run this once — it takes 1–5 minutes depending on your internet speed:

```
ollama pull gemma2:2b
```

> **Want better results?** Pull a larger model instead:
> ```
> ollama pull qwen2.5-coder:7b
> ```
> Then update `OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b` in your `.env` file (Step 3).

---

### Step 3 — Create your `.env` file

**Windows:**
```
copy .env.example .env
```

**Mac / Linux:**
```
cp .env.example .env
```

Now open the `.env` file in any text editor (Notepad, VS Code, etc.) and change these two lines:

```
SECRET_KEY=paste-any-long-random-string-here-minimum-32-characters
JWT_SECRET=paste-a-different-long-random-string-here-minimum-32-chars
```

You can use anything — just make them long and unique. Example:
```
SECRET_KEY=mycodeguardianapp2026secretkeyabcdef1234567890xyz
JWT_SECRET=myjwtsecretkeycodeguardian2026abcdef1234567890qrs
```

> **Everything else in `.env` can stay as the defaults for local development.**

---

### Step 4 — Set up and start the Backend

Open **Terminal 1** and run these commands one by one:

**Windows:**
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --port 8000
```

**Mac / Linux:**
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --port 8000
```

✅ **The backend is ready when you see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

📌 **Important — check the terminal output for your login password:**
```
demo_user_seeded  email=admin@codeguardian.ai  password_hint=CG-xxxx***
```
Write down the `CG-xxxx` password — you'll need it to log in.

> **Leave Terminal 1 running. Do not close it.**

---

### Step 5 — Set up and start the Frontend

Open a **new Terminal 2** (keep Terminal 1 running) and run:

```
cd codeguardian-ai-fixed
cd frontend
npm install --legacy-peer-deps
npm run dev
```

✅ **The frontend is ready when you see:**
```
▲ Next.js 15.1.0
- Local: http://localhost:3000
```

> **Leave Terminal 2 running. Do not close it.**

---

### Step 6 — Open the app

Open your browser and go to:

```
http://localhost:3000
```

**Login with:**
- Email: `admin@codeguardian.ai`
- Password: the `CG-xxxx` password shown in Terminal 1

---

### Step 7 — Run your first analysis

1. Click **Upload** in the left sidebar
2. Choose **GitHub URL** and paste any public repo, e.g.:
   ```
   https://github.com/tiangolo/fastapi
   ```
3. Click **Analyze**
4. Watch the 9 agents run in real time on the progress screen
5. You'll be automatically taken to the results when done

---

## 🐳 OPTION B — Run with Docker (One Command)

This requires [Docker Desktop](https://www.docker.com/products/docker-desktop) to be installed.

### Step 1 — Create `.env`
```
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```
Edit `.env` and set `SECRET_KEY` and `JWT_SECRET` (any long strings).

### Step 2 — Start everything
```
docker compose -f docker/docker-compose.yml up --build
```

### Step 3 — Pull the model (first time only)
Open a second terminal while Docker is running:
```
docker exec -it codeguardian-ollama ollama pull gemma2:2b
```

### Step 4 — Open the app
```
http://localhost:3000
```

Check the Docker logs for your login password:
```
docker logs codeguardian-backend 2>&1 | grep "password_hint"
```

### Stop Docker
```
docker compose -f docker/docker-compose.yml down
```

---

## 🧪 Run the Tests

**Backend tests:**
```
# Windows (with venv activated)
cd codeguardian-ai-fixed
set APP_ENV=test
set SECRET_KEY=test-secret-key-32-chars-padded!!
set JWT_SECRET=test-jwt-secret-32-chars-padded!!!
set DEMO_ADMIN_PASSWORD=TestPass123!
python -m pytest tests/backend/test_api.py -v

# Mac / Linux
cd codeguardian-ai-fixed
APP_ENV=test SECRET_KEY=test-secret-key-32-chars-padded!! \
JWT_SECRET=test-jwt-secret-32-chars-padded!!! \
DEMO_ADMIN_PASSWORD=TestPass123! \
python -m pytest tests/backend/test_api.py -v
```

**Frontend tests:**
```
cd frontend
npx vitest run
```

---

## 🔍 Verify everything is working

**Check the backend is alive:**
```
curl http://localhost:8000/health
```
Expected response:
```json
{"status": "ok", "env": "development", "version": "1.0.0"}
```

**Check the API docs** (development only):
```
http://localhost:8000/docs
```

---

## 🔁 How to restart next time

You do **not** need to reinstall anything after the first time.

**Terminal 1 (backend):**
```
# Windows
cd codeguardian-ai-fixed\backend
.venv\Scripts\activate
cd ..
uvicorn backend.app.main:app --reload --port 8000

# Mac / Linux
cd codeguardian-ai-fixed/backend
source .venv/bin/activate
cd ..
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 (frontend):**
```
cd codeguardian-ai-fixed/frontend
npm run dev
```

---

## ⚙️ Environment Variables Reference

All variables live in your `.env` file. The important ones:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | — | App secret — set to any long random string |
| `JWT_SECRET` | ✅ Yes | — | JWT signing secret — set to a different long string |
| `APP_ENV` | No | `development` | Set to `production` to disable API docs |
| `OLLAMA_DEFAULT_MODEL` | No | `gemma2:2b` | AI model to use |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server address |
| `DATABASE_URL` | No | `sqlite:///./codeguardian.db` | Database location |
| `GITHUB_TOKEN` | No | — | For private GitHub repos or avoiding rate limits |
| `DEMO_ADMIN_PASSWORD` | No | auto-generated | Override the auto-generated admin password |
| `MAX_UPLOAD_MB` | No | `100` | Max file upload size |

---

## 🛠️ Troubleshooting

### "Ollama not found" or model errors
Make sure Ollama is running:
```
ollama serve
```
Then pull the model:
```
ollama pull gemma2:2b
```

### "Port 8000 already in use"
Kill the process using port 8000 and try again, or use a different port:
```
uvicorn backend.app.main:app --reload --port 8001
```
Then update `APP_BASE_URL=http://localhost:8001` in `.env`.

### "npm install fails"
Try clearing the cache:
```
npm cache clean --force
npm install --legacy-peer-deps
```

### "pip install fails"
Make sure your virtual environment is activated (you should see `(.venv)` at the start of your terminal prompt).

### Analysis gets stuck at 0%
Ollama may not be running or the model hasn't been pulled yet:
```
ollama serve            # start Ollama
ollama pull gemma2:2b   # pull model
```

### Login doesn't work
Look in Terminal 1 for the line that says `password_hint=CG-xxxx***` — that is your password.  
Or set a fixed password in `.env`:
```
DEMO_ADMIN_PASSWORD=MyPassword123!
```
Then restart the backend.

### Frontend shows blank page
Make sure the backend is running on port 8000 first, then refresh the browser.

---

## 📁 Project Structure (Quick Reference)

```
codeguardian-ai-fixed/
├── backend/                ← FastAPI Python API
│   ├── app/
│   │   ├── agents/         ← 10 AI agents
│   │   ├── api/            ← REST routes
│   │   ├── core/           ← Config, logging
│   │   ├── db/             ← Database models
│   │   ├── security/       ← Auth, JWT, RBAC
│   │   └── services/       ← LLM, vector DB, reports
│   └── requirements.txt
├── frontend/               ← Next.js 15 UI
│   ├── app/                ← Pages
│   ├── components/         ← UI components
│   ├── hooks/              ← React hooks
│   └── lib/                ← API client, utils
├── docker/                 ← Dockerfiles & compose
├── docs/                   ← Documentation
├── tests/                  ← Test suites
├── .env.example            ← Copy this to .env
├── HOW-TO-RUN.md           ← This file
└── README.md               ← Project overview
```

---

## 🌐 URLs Summary

| URL | What |
|-----|------|
| http://localhost:3000 | Main application |
| http://localhost:3000/login | Login page |
| http://localhost:3000/dashboard | Dashboard |
| http://localhost:3000/upload | Upload & analyze |
| http://localhost:8000/health | Backend health check |
| http://localhost:8000/docs | API docs (dev only) |

---

*CodeGuardian AI — Autonomous Multi-Agent Code Review Platform*  
*MIT License © 2026*
