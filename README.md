# UnFake

**In-context claim verification for Philippine internet users.**

UnFake combines a Chromium Manifest V3 extension with a local FastAPI backend. Select
text or crop a screenshot region, review the extracted claim, and see a verdict with
dated evidence links on the page you are reading.

## Current build: v0.4.0

- Text selection and manual popup input.
- Local screenshot cropping and Tesseract.js OCR with editable text review.
- Client-side English/Filipino/Taglish preprocessing and rule triage; backend revalidation.
- SQLite FTS5 archive with reviewed imports, provenance, and model-tagged vector storage.
- Concurrent archive/live retrieval through a configurable Tavily adapter.
- Configurable Gemini stance evaluation with structured output and citation validation.
- Exact reviewed-claim ratings when no model is configured; honest insufficient-evidence
  responses for unmatched claims. No placeholder citations.
- Optional empirical confidence calibration, stage timings, and evaluation utilities.
- User-triggered page injection through activeTab access, local deadlines, and safe links.

**130 backend tests and 8 extension tests pass.** A real Chrome-for-Testing run has
exercised the backend/archive result flow, client triage, unsafe-source rendering, crop,
local WASM OCR, OCR review/submission, and popup health.

The included archive has **four sourced demonstration records**, all debunks. It is not
a representative benchmark. Live services require keys; semantic search requires indexing;
public confidence stays unavailable until a suitable empirical calibration artifact exists.

## Start on Windows

Requires Python 3.10+ and Chrome or Edge. The setup script also recognizes the local Codex
bundled Python runtime when a standard Python installation is unavailable.

```powershell
powershell -ExecutionPolicy Bypass -File .\Setup-UnFake.ps1
```

Then run `Start-UnFake.cmd`. Keep its terminal open while using the extension.

1. Open `chrome://extensions` or `edge://extensions`.
2. Enable **Developer mode**, choose **Load unpacked**, and select `extension`.
3. Open [the local demo](http://localhost:8000/demo).
4. Highlight its example claim and use **Verify Text with UnFake**, or use **Verify Image /
   Screen Region** to crop the quote card. The popup includes an archived example button.

The demo works without API keys. The backend stays on your machine at
`http://localhost:8000`; [API documentation](http://localhost:8000/docs) and
[health](http://localhost:8000/api/v1/health) are available while it is running.

For manual Python setup or provider configuration, see [IMPLEMENTATION.md](docs/IMPLEMENTATION.md).

## Enable live search and semantic assessment

Set `TAVILY_API_KEY` and `GEMINI_API_KEY` in `backend/.env` and restart the backend. Set
`EMBEDDING_PROVIDER=gemini` and index the archive to enable cloud semantic retrieval:

```powershell
cd backend
& ..\.venv\Scripts\python.exe -m scripts.seed_archive --embed
```

Optional local embeddings use `requirements-semantic.txt` and `EMBEDDING_PROVIDER=local`.
Provider adapters are tested with mocked responses; a live provider run still needs
valid keys. See the implementation guide for model settings, indexing, and limitations.

## Tests and evaluation

```powershell
cd backend
& ..\.venv\Scripts\python.exe -m pytest tests -q
cd ..
node --test tests/extension.test.cjs
```

The browser test requires Playwright and Chrome for Testing; instructions are in the
implementation guide. GitHub Actions runs backend checks on Python 3.10/3.12 and the
extension tests. CI execution on GitHub has not been claimed by this local build.

Measurement utilities support labeled claim benchmarks, OCR CER/WER by resolution,
and held-out confidence calibration. A representative corpus, independently reviewed
labels, and a participant comparison against manual search are still required for the
thesis. Development smoke-test scores are not research accuracy claims.

## Privacy and interpretation

Only explicit user actions start processing. OCR runs locally. Chrome temporarily captures
the visible viewport inside the extension and then crops it; images are not uploaded to
the backend. After review, the claim text goes to the local backend. Configured providers
receive the claim and relevant source excerpts as described in the implementation guide.
No browsing-history collection, cookie access, or continuous webpage scanning is implemented.

Supported, contradicted, mixed, and insufficient-evidence results are assistive assessments.
Check source dates and context. OCR recognition confidence is separate from calibrated
verdict reliability; missing coverage does not mean a claim is false.

## Documentation and provenance

- [Current implementation, setup, privacy, and research workflow](docs/IMPLEMENTATION.md)
- [Original handover with current implementation update](docs/HANDOVER.md)
- [API contract](docs/API_CONTRACT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Starter archive provenance](backend/data/README.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

Original project: [fafii2/UnFake](https://github.com/fafii2/UnFake).
Developed as an academic research project. The upstream repository does not currently
include a project-wide LICENSE file; third-party assets retain their own licenses.
