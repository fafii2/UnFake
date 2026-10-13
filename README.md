# UnFake

**AI-Assisted, In-Context Misinformation Verification Browser Extension**

UnFake is a Chromium browser extension that helps Filipino internet users evaluate questionable online claims. It captures text (or text-containing images), retrieves evidence from local Philippine fact-checking archives and live web sources, evaluates the evidence using a RAG pipeline, and displays an understandable result directly within the browser tab.

> **Note:** UnFake is an assistive verification tool, not an infallible fake-news detector. It acknowledges insufficient, conflicting, or outdated evidence rather than inventing certainty.

## Project Structure

```
UnFake/
├── extension/          # Chrome extension (Manifest V3)
│   ├── manifest.json
│   ├── popup/          # Extension popup UI
│   ├── content/        # Content scripts (injected into pages)
│   └── background/     # Service worker
├── backend/            # Python FastAPI backend
│   ├── main.py         # Application entry point
│   ├── api/            # API routes and schemas
│   ├── services/       # Business logic modules
│   ├── db/             # Database layer
│   └── tests/          # pytest test suite
└── docs/               # Project documentation
```

## Quick Start

### Prerequisites

- Python 3.10+
- Google Chrome or Microsoft Edge
- Git

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env

# Start the development server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` and interactive docs at `http://localhost:8000/docs`.

### Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked**.
4. Select the `extension/` folder inside this repository.
5. The UnFake icon should appear in your browser toolbar.

### Usage

1. Select any text on a webpage.
2. Right-click and choose **"Verify with UnFake"**.
3. A results modal will appear on the page with the verification result.

## API Documentation

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for the full API specification.

## Development

### Running Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system architecture overview.

## License

This project is developed as an academic thesis project.
