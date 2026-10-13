# UnFake 🔍🛡️

**AI-Assisted, In-Context Misinformation Verification Browser Extension**

UnFake is an academic research and software development project designed to assist Filipino internet users in evaluating questionable online claims, altered screenshots, quote cards, and social media posts.

Instead of requiring users to leave their current webpage to cross-reference multiple fact-checking portals manually, UnFake enables users to submit claims for verification **directly within the active browser tab**.

> [!IMPORTANT]
> **Research & Assistive Tool Notice**  
> UnFake is an assistive verification aid, not an infallible automated truth oracle. The system acknowledges insufficient, conflicting, or outdated evidence rather than inventing false certainty.

---

## 📑 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Start the Backend Server](#2-start-the-backend-server)
  - [3. Install the Extension in Your Browser](#3-install-the-extension-in-your-browser)
- [How to Use UnFake](#-how-to-use-unfake)
  - [Method A: Highlight & Right-Click (In-Page)](#method-a-highlight--right-click-in-page)
  - [Method B: Manual Verification via Popup](#method-b-manual-verification-via-popup)
- [Understanding the Results](#-understanding-the-results)
- [Running Automated Tests](#-running-automated-tests)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Development Roadmap](#-development-roadmap)
- [License](#-license)

---

## ✨ Features

- **In-Context Verification**: Highlight text on any website (social media, news articles, forums) and verify it without switching tabs.
- **Minimal Privacy Footprint**: Built with Chrome's Manifest V3. UnFake **never** tracks browsing history, reads cookies, or accesses form passwords. It only processes text explicitly selected or submitted by the user.
- **Clean In-Page Modal**: Displays results in a modern **White & Navy Blue** modal overlay with responsive animations, color-coded verdict badges, and clickable citations.
- **Rule-Based Triage Engine**: Pre-filters opinions, rhetorical questions, and casual Tagalog/Taglish slang to avoid wasting computational resources on non-verifiable content.
- **Multi-Source Evidence**: Architected to consult Philippine fact-checking archives (Tsek.ph, VERA Files) alongside live web retrieval.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  BROWSER EXTENSION (Manifest V3 - Client)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Popup UI   │  │  Content     │  │  Background      │  │
│  │  (popup.html)│  │  Script      │  │  Service Worker  │  │
│  │              │  │  (content.js)│  │  (service-worker)│  │
│  │  - Status dot│  │  - Selection │  │  - Context menu  │  │
│  │  - Manual box│  │  - Modal UI  │  │  - API dispatcher│  │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬────────┘  │
│         │                  │                     │           │
│         └──── chrome.runtime.sendMessage ────────┘           │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP POST (/api/v1/verify)
                                ▼
┌─────────────────────────────────────────────────────────────┐
│  PYTHON FASTAPI BACKEND (Server)                            │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  REST API Router (/api/v1)                            │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                              │                              │
│      ┌───────────────────────┼───────────────────────┐      │
│      ▼                       ▼                       ▼      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │ Preprocessor │────▶│ Triage Engine│────▶│ RAG Pipeline │ │
│  │ (Clean/Norm) │     │ (Filter Rules│     │ (Evaluation) │ │
│  └──────────────┘     └──────────────┘     └──────┬───────┘ │
│                                                   │         │
│                        ┌──────────────────────────┴──────┐  │
│                        ▼                                 ▼  │
│               ┌──────────────────┐             ┌──────────┐ │
│               │ Local Fact-Check │             │ Live Web │ │
│               │ Archive (SQLite) │             │ Search   │ │
│               └──────────────────┘             └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

Make sure you have the following installed on your computer:

1. **Chromium-based Browser**: Google Chrome, Microsoft Edge, Brave, or Opera.
2. **Python 3.10 or higher**: [Download Python](https://www.python.org/downloads/) *(make sure to check "Add Python to PATH" during installation)*.
3. **Git**: [Download Git](https://git-scm.com/downloads).

---

## 🚀 Quick Start Guide

### 1. Clone the Repository

Open your terminal (PowerShell, Command Prompt, or bash) and run:

```bash
git clone https://github.com/fafii2/UnFake.git
cd UnFake
```

---

### 2. Start the Backend Server

The extension communicates with a local FastAPI backend. Follow these steps to get it running:

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On macOS / Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Create your local environment configuration file
copy .env.example .env    # On Windows
# cp .env.example .env    # On macOS/Linux

# Start the server
uvicorn main:app --reload --port 8000
```

Once running, your backend is live at:
- **API Base**: `http://localhost:8000`
- **Interactive API Documentation (Swagger)**: `http://localhost:8000/docs`

> [!TIP]
> Keep this terminal window open while using the browser extension.

---

### 3. Install the Extension in Your Browser

You do not need to download anything from the Chrome Web Store. You can load UnFake directly in Developer Mode:

1. Open **Google Chrome** (or Microsoft Edge).
2. Navigate to the extensions page:
   - In Chrome, enter `chrome://extensions/` in the address bar.
   - In Edge, enter `edge://extensions/`.
3. In the top-right corner, toggle **Developer mode** to **ON**.
4. Click the **Load unpacked** button in the top-left corner.
5. In the file picker, select the **`extension`** folder inside your cloned `UnFake` repository:
   ```
   UnFake/extension/
   ```
6. The **UnFake** icon (shield with verification emblem) will now appear in your browser's extension list!
7. *(Recommended)* Click the puzzle piece icon 🧩 in Chrome's toolbar and **pin** UnFake to your browser bar for easy access.

---

## 🖱️ How to Use UnFake

### Method A: Highlight & Right-Click (In-Page)

1. Open any webpage containing a claim you want to check (e.g., a news site, Facebook post, or blog).
2. **Highlight / select the text** of the claim with your mouse cursor.
3. **Right-click** on the highlighted text.
4. Select **"Verify with UnFake"** from the context menu.
5. A loading spinner will appear, followed by the **in-page results modal** showing the verdict, explanation, and evidence sources.
6. Click the **&times;** button, click outside the modal, or press **Escape** to dismiss it.

### Method B: Manual Verification via Popup

1. Click the **UnFake icon** in your browser toolbar.
2. The popup will check your backend connection (it should display a green **"Backend online"** dot).
3. Paste or type any claim into the **Manual verification** text box.
4. Click **Verify Claim**.
5. The result will immediately render on your active webpage tab.

---

## 🏷️ Understanding the Results

UnFake classifies evaluated claims into four primary categories:

| Verdict Badge | Meaning | Description |
|---|---|---|
| **✅ Supported** | `supported` | High-quality, reputable reporting or official records substantiate the claim. |
| **❌ Contradicted** | `contradicted` | Established fact-checks or primary evidence directly disprove the assertion. |
| **⚠️ Mixed Evidence** | `mixed` | Sources report conflicting information, or the claim contains both true and false elements. |
| **❓ Insufficient Evidence** | `insufficient_evidence` | Reliable sources have not yet covered or verified the claim. UnFake will never assume a missing result means the claim is false. |
| **ℹ️ Not a Factual Claim** | `triage_rejected` | The text is an opinion, rhetorical question, emotional remark, or casual slang rather than a verifiable statement. |

---

## 🧪 Running Automated Tests

The backend includes a comprehensive `pytest` suite testing data validation, Unicode handling (Filipino/Tagalog text), edge cases, and API contracts.

To run the test suite:

```bash
cd backend

# Ensure your venv is active
pytest tests/ -v
```

All 25 tests should pass:

```
tests/test_api.py::TestVerifyEndpoint::test_verify_valid_text_claim PASSED
tests/test_api.py::TestVerifyEndpoint::test_verify_handles_unicode PASSED
...
======================== 25 passed in 0.25s ========================
```

---

## 📁 Project Structure

```
UnFake/
├── extension/                       # Chromium Browser Extension (MV3)
│   ├── manifest.json                # Extension configuration & permissions
│   ├── icons/                       # Extension app icons (16px, 48px, 128px)
│   ├── popup/                       # Toolbar popup UI
│   │   ├── popup.html               # Popup layout & health indicator
│   │   ├── popup.css                # White & Navy Blue popup styling
│   │   └── popup.js                 # Health check & manual submission logic
│   ├── content/                     # In-page content scripts & styles
│   │   ├── content.js               # Modal injector & result renderer
│   │   ├── content.css              # Isolated styles (prefixed 'unfake-')
│   │   └── text-selection.js        # Text extraction helper
│   └── background/
│       └── service-worker.js        # Context menu setup & API dispatcher
│
├── backend/                         # Python FastAPI Backend
│   ├── main.py                      # Application entrypoint & CORS middleware
│   ├── config.py                    # Environment settings singleton
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment template
│   ├── api/
│   │   ├── router.py                # Endpoint routes (/api/v1/verify)
│   │   └── schemas.py               # Pydantic v2 contract models
│   ├── services/
│   │   ├── preprocessor.py          # Text normalization & noise cleaning
│   │   ├── triage.py                # Rule-based claim filter
│   │   ├── retrieval.py             # Local archive & web search coordinator
│   │   └── evaluator.py             # RAG evaluation service
│   ├── db/
│   │   ├── database.py              # SQLite connection manager
│   │   └── models.py                # Database schemas
│   └── tests/                       # Automated test suite
│       ├── test_api.py              # Contract & validation tests
│       ├── test_preprocessor.py     # Cleaning & normalization tests
│       └── test_triage.py           # Triage engine tests
│
└── docs/                            # Detailed Technical Documentation
    ├── API_CONTRACT.md              # Complete JSON contract documentation
    ├── ARCHITECTURE.md              # Architecture diagrams & component responsibilities
    └── SETUP.md                     # Developer setup & configuration guide
```

---

## 🔧 Troubleshooting

### 1. The popup says "Backend unreachable"
- Make sure your FastAPI backend is running: `uvicorn main:app --reload --port 8000`.
- Verify the server is accessible in your browser at `http://localhost:8000/`.

### 2. The context menu item "Verify with UnFake" doesn't appear
- Open `chrome://extensions/` and click the **Reload icon (🔄)** on the UnFake card.
- Make sure you actually **selected text** before right-clicking; the context menu only appears when text is highlighted.

### 3. Changes to code or styles aren't showing up
- Whenever you edit files in `extension/`, go to `chrome://extensions/` and click **Reload (🔄)** on UnFake.
- **Refresh the webpage tab** (`Ctrl + R` or `F5`) where you are testing, as content scripts do not automatically update in already-opened tabs.

### 4. CORS errors in the browser console
- In `backend/.env`, verify that `ALLOWED_ORIGINS` includes your extension ID:
  ```
  ALLOWED_ORIGINS=chrome-extension://<your-extension-id>,http://localhost:3000
  ```
- Restart the FastAPI server after editing `.env`.

---

## 🗺️ Development Roadmap

- [x] **Milestone 1 — Project Foundation** *(Completed)*: MV3 extension, FastAPI skeleton, CORS configuration, Pydantic contract, 25 tests, White & Navy Blue UI.
- [ ] **Milestone 2 — Text Input & Triage Engine** *(Next)*: Heuristic filtering for English, Tagalog, and Taglish claims; noise & quote stripping.
- [ ] **Milestone 3 — Image Input & Client-Side OCR**: Manual screenshot cropping overlay with Tesseract.js integration.
- [ ] **Milestone 4 — Evidence Retrieval**: Philippine fact-check archive (SQLite + vector search) and configurable live web search.
- [ ] **Milestone 5 — Evidence Evaluation (RAG)**: Multi-source comparison, grounded verdict generation, and citation formatting.
- [ ] **Milestone 6 — Thesis Evaluation**: End-to-end latency benchmarks, OCR accuracy metrics, and triage classification evaluation.

---

## 📄 License & Attribution

Developed as an academic software development and thesis research project.  
Author: [fafii2](https://github.com/fafii2)  
Contact: `kenhautea37@gmail.com`
