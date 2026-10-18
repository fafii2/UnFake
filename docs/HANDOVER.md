# UnFake — Project Handover & Progress Documentation 🔍🛡️

> **Notice for Incoming Teammate**: This document summarizes the complete project context, what has been built and tested to date, key design decisions, known hurdles and how they were solved, and an actionable roadmap for upcoming milestones.

---

## 📌 1. Project Overview & Core Philosophy

**UnFake** is an academic research and software development project designed to assist Filipino internet users in evaluating questionable online claims, viral posts, quote cards, and social media screenshots.

### Key Tenets
1. **In-Context Verification**: Users should never have to switch tabs, open multiple search engines, or copy-paste claims across separate portals. Everything happens inside the active webpage tab.
2. **Assistive Aid, Not an Infallible Oracle**: The system explicitly acknowledges when evidence is insufficient, conflicting, or outdated, rather than hallucinating certainty.
3. **Strict Privacy Footprint**: Built on Chrome Manifest V3. UnFake does **not** track browsing activity, inspect form passwords, or read webpage contents indiscriminately. It only inspects text or image regions explicitly selected/cropped by the user.
4. **Multilingual Philippine Context**: Designed specifically for Philippine political discourse, news topics, government agencies, and code-switched Filipino/Taglish text.

---

## 🚀 2. Current Status & Progress Summary

| Milestone | Scope | Status | Notes |
|---|---|---|---|
| **Milestone 1** | System Foundation & Stub Architecture | **DONE** ✅ | MV3 extension, FastAPI backend, Pydantic contracts, Navy & White UI, initial tests. |
| **Milestone 2** | Text Preprocessing & Rule-Based Triage Engine | **DONE** ✅ | Text normalizer (quotes, broadcast prefixes, noise) + multilingual triage engine (English/Tagalog/Taglish). |
| **Milestone 3** | Image Cropping & Offline OCR (Tesseract.js) | **DONE** ✅ | Interactive crop overlay, MV3 offscreen document for WASM/WebWorker, local `eng.traineddata.gz`, OCR review modal. |
| **Milestone 4** | Evidence Retrieval Pipeline | *PENDING* ⏳ | Local Philippine fact-check archive (SQLite/Vector) + Live Web Search fallback. |
| **Milestone 5** | Evidence Evaluation (RAG Pipeline) | *PENDING* ⏳ | Multi-source evidence synthesis, grounded verdict generation, citation builder. |
| **Milestone 6** | Thesis Evaluation & Benchmarking | *PENDING* ⏳ | OCR accuracy, triage precision/recall, latency profiling. |

**Current Test Suite**: **71 tests passing** (`pytest backend/tests/ -v`).

---

## 🏗️ 3. What We Have Built & How It Works

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CHROME EXTENSION (Manifest V3)                       │
│                                                                         │
│  ┌────────────────────────┐         ┌────────────────────────────────┐  │
│  │ Popup (popup.html/.js) │         │ Content Scripts (content.js)   │  │
│  │  - Health status dot   │         │  - Text selection extraction   │  │
│  │  - Manual input field  │         │  - Floating result modal       │  │
│  └───────────┬────────────┘         │  - OCR review modal            │  │
│              │                      └───────────────┬────────────────┘  │
│              │                                      │                   │
│              ▼                                      ▼                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Background Service Worker (background/service-worker.js)          │  │
│  │  - Context menu actions ("Verify Text", "Verify Image / Screen")  │  │
│  │  - Viewport screenshots via chrome.tabs.captureVisibleTab         │  │
│  │  - Offscreen document lifecycle management                        │  │
│  │  - REST API dispatcher to backend                                 │  │
│  └──────────────────┬───────────────────────────────┬────────────────┘  │
│                     │                               │                   │
│                     ▼                               ▼                   │
│       ┌───────────────────────────┐   ┌───────────────────────────┐     │
│       │ Offscreen Doc (WASM OCR)  │   │ HTTP POST /api/v1/verify  │     │
│       │  - Tesseract.js Worker    │   │ (JSON Request & Response) │     │
│       │  - Canvas viewport crop   │   └─────────────┬─────────────┘     │
│       │  - Offline eng traineddata│                 │                   │
│       └───────────────────────────┘                 │                   │
└─────────────────────────────────────────────────────┼───────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (Python 3.10+)                      │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ REST API Router (/api/v1/verify) [backend/api/router.py]          │  │
│  └──────────────────┬────────────────────────────────────────────────┘  │
│                     │                                                   │
│                     ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 1. Text Preprocessor [backend/services/preprocessor.py]           │  │
│  │    - Unicode normalization (NFC)                                  │  │
│  │    - Typographic quote normalization                              │  │
│  │    - Enclosing quote and bracket stripping                        │  │
│  │    - Broadcast prefix stripping ("BREAKING:", "[JUST IN]", etc.)  │  │
│  │    - Punctuation collapsing (??? -> ?, !!! -> !)                  │  │
│  └──────────────────┬────────────────────────────────────────────────┘  │
│                     │                                                   │
│                     ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 2. Rule-Based Triage Engine [backend/services/triage.py]          │  │
│  │    - English, Tagalog & Taglish classification                    │  │
│  │    - Filters out opinions, inquiries, casual slang, fragments     │  │
│  │    - Detects factual anchors (entities, metrics, dates, actions)  │  │
│  │    - Rejects early if non-verifiable (saves compute/LLM budget)   │  │
│  └──────────────────┬────────────────────────────────────────────────┘  │
│                     │                                                   │
│         ┌───────────┴───────────┐                                       │
│         │ (If Verifiable)       │ (If Non-Verifiable)                   │
│         ▼                       ▼                                       │
│  ┌──────────────┐        ┌───────────────────────────────────────────┐  │
│  │ Milestones   │        │ Early Exit Response                       │  │
│  │ 4 & 5 (RAG)  │        │ status: "triage_rejected"                 │  │
│  │ [STUBS]      │        │ explanation: Why it cannot be verified    │  │
│  └──────────────┘        └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 4. Detailed Component Breakdown

### A. Chrome Extension (Manifest V3)
- **`extension/manifest.json`**:
  - Permissions: `activeTab`, `contextMenus`, `offscreen`, `scripting`, `tabs`.
  - Host Permissions: `<all_urls>`, `http://localhost:8000/*`.
  - CSP: `"extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self';"`.
- **`extension/background/service-worker.js`**:
  - Sets up right-click menus:
    1. `"Verify Text with UnFake"` (triggers on selected text).
    2. `"Verify Image / Screen Region"` (triggers on page, image, or frame).
  - Handles message dispatching between popup, content script, and offscreen document.
- **`extension/content/image-crop.js` & `content.css`**:
  - Injects a full-viewport SVG/Canvas overlay when image verification is initiated.
  - Interactive crosshair cursor with click-and-drag selection box.
  - Accurately captures bounding coordinates and viewport scaling (`window.devicePixelRatio`, `naturalWidth` vs `viewportWidth`).
- **`extension/offscreen/offscreen.html` & `offscreen.js`**:
  - **Why Offscreen?** In Chrome Manifest V3, service workers cannot access DOM APIs (like `<canvas>` and `document`), and web workers loaded in arbitrary web pages are blocked by the host page's Content Security Policy (CSP). The `offscreen` API provides a sandboxed extension window where Canvas cropping and Tesseract.js WASM execution run safely.
  - Bundles local `tesseract.min.js`, `worker.min.js`, `tesseract-core-lstm.wasm.js`, and `eng.traineddata.gz` in `extension/lib/`.
  - Configured with `workerBlobURL: false` to comply with MV3 security restrictions.
- **`extension/content/content.js`**:
  - Manages the floating White & Navy Blue verification modal.
  - Renders loading spinner, OCR review dialog (allows user to correct text before submitting), and final verdict cards.
  - Color-coded verdict badges:
    - Supported (`#10b981` Emerald Green)
    - Contradicted (`#ef4444` Crimson Red)
    - Mixed Evidence (`#f59e0b` Amber)
    - Insufficient Evidence (`#6b7280` Slate Gray)
    - Triage Rejected (`#3b82f6` Blue Info)

### B. Python FastAPI Backend
- **`backend/main.py`**:
  - FastAPI application entry point with CORS middleware configured for Chrome extension origins.
- **`backend/api/router.py`**:
  - Exposes `POST /api/v1/verify` and `GET /api/v1/health`.
- **`backend/api/schemas.py`**:
  - Strict Pydantic v2 schemas: `VerifyRequest`, `VerifyResponse`, `TriageResult`, `EvidenceItem`, `Verdict`, `VerifyStatus`.
- **`backend/services/preprocessor.py`**:
  - Cleans input noise: strips quotation marks, square brackets, leading broadcast tokens (`BREAKING NEWS:`, `[JUST IN]`, `BALITA:`), and collapses repeated punctuation (`???` $\to$ `?`).
- **`backend/services/triage.py`**:
  - Rule-based regex heuristic engine that categorizes inputs into:
    - `FACTUAL_ASSERTION`: Passes to verification.
    - `UNCERTAIN_BORDERLINE`: Passes to verification (with attribution note).
    - `QUESTION`: Rejected (interrogatives like *Who, What, Bakit, Paano, Totoo ba na*).
    - `OPINION`: Rejected (evaluatives like *I think, Sa tingin ko, mas masarap, the best*).
    - `CASUAL_COMMENTARY`: Rejected (slang like *charot, eme, beh, yarn, lol*).
    - `TOO_SHORT`: Rejected (fewer than 4 words).
  - Anchors on named entities (Philippine politicians, departments like DOH, DepEd, DSWD, Comelec), numbers/monetary values (`₱`, `%`, `billion`), and verifiable action predicates (*signed, enacted, arrested, approved*).

---

## 💡 5. Feature Ideas & How We Planned to Implement Them

### 1. Offline Philippine Fact-Check Archive (Milestone 4)
- **Concept**: A pre-indexed database of verified claims from Philippine fact-checking coalitions (Tsek.ph, VERA Files, Rappler Fact Check).
- **Implementation Strategy**:
  - **Storage**: SQLite database (`backend/db/database.py`).
  - **Search**: Hybrid search combining BM25 keyword search (via SQLite FTS5) with semantic vector search (e.g., using `sentence-transformers` `all-MiniLM-L6-v2` or `paraphrase-multilingual-MiniLM-L12-v2`).
  - **Schema**: Claim text, normalized claim, fact-check verdict, original publisher, source URL, explanation excerpt, publication date, embedding vector.

### 2. Live Web Search Fallback (Milestone 4)
- **Concept**: If the local archive does not have a high-confidence match, query trusted search APIs.
- **Implementation Strategy**:
  - Query Google Custom Search JSON API, Tavily, or DuckDuckGo.
  - Restrict queries to reputable Philippine news organizations (e.g., Inquirer, Philstar, GMA News, ABS-CBN News, Rappler, PNA).
  - Extract top 3–5 search snippets for evidence evaluation.

### 3. RAG Evidence Evaluator (Milestone 5)
- **Concept**: Feed the user's claim + retrieved evidence snippets into an LLM to generate an objective verdict and explanation.
- **Implementation Strategy**:
  - Use Google Gemini API (or a lightweight local model via Ollama).
  - Enforce strict system prompt instructions:
    - Never assume unverified claims are automatically false.
    - If evidence is conflicting, classify as `mixed`.
    - If no relevant reports exist, classify as `insufficient_evidence`.
    - Include direct markdown links to citations.

### 4. Tagalog Language OCR Support (Future Enhancement)
- Currently, `eng.traineddata.gz` is bundled. While English OCR reads many Latin-alphabet Filipino words well, adding `tgl.traineddata.gz` or a bilingual model will improve recognition of diacritics and Tagalog-specific orthography on quote cards.

---

## 🛠️ 6. How to Continue (Next Steps for the Teammate)

### Step 1: Start Milestone 4 (Evidence Retrieval)
1. **Define the Database Schema**:
   - Open `backend/db/models.py` and create an `EvidenceRecord` table (SQLAlchemy or raw SQLite).
   - Fields: `id`, `claim_text`, `verdict`, `publisher`, `source_url`, `published_date`, `snippet`, `embedding`.
2. **Implement Archive Loader / Seeder**:
   - Create a script `backend/scripts/seed_archive.py` that populates sample fact-checks from public Philippine fact-checks (e.g., CSV/JSON dumps of Tsek.ph or VERA Files articles).
3. **Build the Retrieval Function**:
   - Open `backend/services/retrieval.py` and replace the stub `retrieve_evidence(claim: str)`.
   - Implement keyword match (`LIKE` or SQLite FTS5) and vector similarity.
   - Add live web search fallback when archive similarity score $< 0.70$.

### Step 2: Implement Milestone 5 (RAG Evaluator)
1. Open `backend/services/evaluator.py` and replace the stub `evaluate_claim(claim: str, evidence: list[dict])`.
2. Integrate the LLM client (e.g. `google-genai` or `openai` SDK).
3. Build the evaluation prompt and parse the JSON output into `Verdict` (`supported`, `contradicted`, `mixed`, `insufficient_evidence`) and citations.

### Step 3: Run and Expand the Test Suite
- Run existing tests: `pytest backend/tests/ -v`.
- Add new test files:
  - `backend/tests/test_retrieval.py` (mocked DB and search results).
  - `backend/tests/test_evaluator.py` (mocked LLM reasoning).

---

## 💻 7. Developer Quick Reference

### Running the Backend
```bash
cd backend
# Activate virtualenv (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# Run FastAPI server
uvicorn main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### Loading / Reloading the Extension
1. Open Chrome $\to$ `chrome://extensions/`.
2. Ensure **Developer mode** is **ON**.
3. Click **Load unpacked** $\to$ select `d:\Projects\UnFake\extension`.
4. After editing extension files, click the **Reload (🔄)** icon on the UnFake extension card, and **refresh the browser tab** where you are testing.

### Running Tests
```bash
cd backend
pytest tests/ -v
```
*(All 71 tests must pass before committing).*
