# UnFake

**In-context claim verification for Philippine internet users.**

UnFake combines a Chromium Manifest V3 extension with a local FastAPI backend. Select
text or crop a screenshot region, review the extracted claim, and see a verdict with
dated evidence links on the page you are reading.

## Current build: v0.4.1

- Text selection and manual popup input.
- Local screenshot cropping and Tesseract.js OCR with editable text review.
- Saved PNG/JPEG/WebP screenshot input, processed locally before text review.
- An explicit live-connection check for search and evaluation, cached for five minutes.
- Short browser polling requests while live verification finishes on the backend.
- One retry for temporary Gemini service failures; evidence remains visible on failure.
- Client-side English/Filipino/Taglish preprocessing and rule triage; backend revalidation.
- SQLite FTS5 archive with reviewed imports, provenance, and model-tagged vector storage.
- Concurrent archive/live retrieval through a configurable Tavily adapter.
- Configurable Gemini stance evaluation with structured output and citation validation.
- Exact reviewed-claim ratings when no model is configured; honest insufficient-evidence
  responses for unmatched claims. No placeholder citations.
- Optional empirical confidence calibration, stage timings, and evaluation utilities.
- User-triggered page injection through activeTab access, local deadlines, and safe links.

See [the presentation checklist](docs/PRESENTATION.md) for the current validation
results and remaining browser checks. Live API checks are separate from unit tests;
neither is an accuracy benchmark.

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
3. Open Facebook or a news article, then open UnFake and click **Check live connections**.
4. Paste one factual statement and choose **Verify Text Claim**, or select it on the page
   and right-click **Verify Text with UnFake**.
5. For a post image, choose **Crop text from this page** or select a saved screenshot.
   Review and correct the extracted text, then verify it.

An optional [local development page](http://127.0.0.1:8001/demo) remains available for
offline archive testing. Live news checking requires working search and model keys.
The backend stays on your machine at
`http://127.0.0.1:8001`; [API documentation](http://127.0.0.1:8001/docs) and
[health](http://127.0.0.1:8001/api/v1/health) are available while it is running.

For manual Python setup or provider configuration, see [IMPLEMENTATION.md](docs/IMPLEMENTATION.md).

## Enable live search and semantic assessment

Set `TAVILY_API_KEY` and `GEMINI_API_KEY` in `backend/.env` and restart the backend. Set
`EMBEDDING_PROVIDER=gemini` and index the archive to enable cloud semantic retrieval:

```powershell
cd backend
& ..\.venv\Scripts\python.exe -m scripts.seed_archive --embed
```

Optional local embeddings use `requirements-semantic.txt` and `EMBEDDING_PROVIDER=local`.
The default evaluation model is `gemini-3.5-flash-lite`. On November 19, a full API
request for "The Philippines has 7,641 islands." returned a grounded `supported`
assessment using Gemini and five live-search sources in 16.079 seconds. This is a
connection smoke test, not an accuracy benchmark. See the implementation guide for
settings, indexing, and limitations. Check provider connections from `backend` with:

```powershell
& ..\.venv\Scripts\python.exe -m scripts.check_providers
```

Keys remain in the backend `.env` file, never in the browser or tracked source.

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
