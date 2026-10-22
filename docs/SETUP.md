# UnFake — Setup Guide

> For v0.4.0, start with [IMPLEMENTATION.md](IMPLEMENTATION.md), which documents the
> Windows setup/launcher, live provider settings, semantic indexing, browser tests,
> privacy behavior, and evaluation workflow. The manual backend setup below remains valid.

## Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Google Chrome** or **Microsoft Edge** (latest version)
- **Git** — [Download](https://git-scm.com/)

---

## Backend Setup

### 1. Create a virtual environment

```bash
cd backend
python -m venv venv
```

### 2. Activate it

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env
```

Edit `.env` and update `ALLOWED_ORIGINS` with your extension's ID (see below).

### 5. Start the server

```bash
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API docs (Swagger UI).

### 6. Run tests

```bash
pytest tests/ -v
```

---

## Extension Setup

### 1. Load the extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder

### 2. Find your extension ID

After loading, Chrome shows the extension ID below the extension name (e.g., `abcdefghijklmnopqrstuvwxyz123456`).

### 3. Update CORS (backend)

Add your extension ID to the `.env` file:

```
ALLOWED_ORIGINS=chrome-extension://your-extension-id-here
```

Restart the backend server.

### 4. Test the extension

1. Navigate to any webpage
2. Select some text
3. Right-click → **"Verify with UnFake"**
4. A results modal should appear on the page

---

## Troubleshooting

### "Backend unreachable" in the popup

- Is the backend running? (`uvicorn main:app --reload --port 8000`)
- Is it running on port 8000?

### Context menu doesn't appear

- Is the extension loaded? Check `chrome://extensions/`
- Try reloading the extension (click the reload icon)
- Did you select text before right-clicking?

### CORS errors in the console

- Add your extension ID to `ALLOWED_ORIGINS` in `.env`
- Restart the backend server after changing `.env`

### Extension shows errors

- Open Chrome DevTools → Console tab for the webpage
- Open `chrome://extensions/` → click "service worker" to see background logs
