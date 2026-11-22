# UnFake v0.4.1: implementation and remaining research work

For the live Facebook/news workflow and current validation limits, start with
[PRESENTATION.md](PRESENTATION.md). This update adds saved screenshot input, explicit
provider readiness checks, asynchronous live verification, and transient-model retries.

This build follows the objectives in the supplied thesis chapters. It is a runnable
development build; it does not establish the thesis hypothesis or claim calibrated
accuracy without research data.

## Implemented

- User-triggered Chromium MV3 interface. `activeTab` grants temporary page access.
  No broad permanent host access or automatic injection on every page.
- Text selection, popup entry, and screenshot-region OCR through an offscreen document
  with bundled English Tesseract assets. Extracted text is reviewed before submission.
- Client normalization and multilingual rule triage before any verification request.
  Python repeats validation for direct callers. Generated regex vocabulary and shared
  bilingual fixtures keep the two implementations aligned.
- SQLite FTS5 archive, reviewed JSON import, publication/retrieval dates, original
  ratings, provenance, and canonical links. Dense vectors are model-tagged and searched
  by cosine similarity without a SQLite extension binary.
- Concurrent archive and Tavily retrieval, explicit partial failures, canonical URL
  deduplication, and request-scoped evidence IDs (`S1`, etc.).
- Gemini structured stance assessment with Pydantic parsing, source-ID validation,
  exact-snippet quote checks, verdict/stance consistency, deadlines, and an instruction
  to treat claims and sources as untrusted data. These controls do not prove model
  reasoning is correct.
- Offline exact-claim evaluation reuses reviewed ratings only for the same assertion
  or reviewed translation. Similarity alone cannot assign a verdict. Missing evidence
  produces an explicit insufficient-evidence assessment.
- Optional isotonic reliability calibration fitted from labeled predictions and bound
  to the model. Public confidence stays null without an applicable calibration artifact.
- Stage timings, a benchmark runner, OCR CER/WER calculation, backend/extension tests,
  and a real Chromium test of sourced verification, OCR, rendering, and popup health.

## Windows setup

1. From the repository, run `powershell -ExecutionPolicy Bypass -File .\Setup-UnFake.ps1`.
   It prepares an isolated environment, installs dependencies, creates `.env` if absent,
   and imports the starter archive. Existing `.env` values are preserved.
2. Run `Start-UnFake.cmd` and keep its window open.
3. In `chrome://extensions` or `edge://extensions`, enable Developer mode, choose
   **Load unpacked**, and select the repository's `extension` folder.
4. Open Facebook or a news article, run **Check live connections** in UnFake, then
   use copied text, a screenshot crop, or saved screenshot input. The `/demo` page
   remains an optional offline development fixture.

The backend binds only to the local machine. API documentation is at `/docs`; health is
available at `/` and `/api/v1/health`.

## Live verification and semantic retrieval

Edit `backend/.env` locally. Keep keys out of chat, Git, and the extension:

```dotenv
TAVILY_API_KEY=your_tavily_key
GEMINI_API_KEY=your_gemini_key
LLM_MODEL=gemini-3.5-flash-lite
EMBEDDING_PROVIDER=gemini
```

Restart the backend. From `backend`, index the archive:

```powershell
& ..\.venv\Scripts\python.exe -m scripts.seed_archive --embed
```

Indexing sends reviewed archive text to the embedding provider and stores vectors
locally. Provider calls use their normal quotas/pricing. Legacy `SEARCH_API_KEY` and
`LLM_API_KEY` remain aliases; `SEARCH_ENGINE_ID` is unused by the Tavily adapter.

For local embeddings, install `requirements-semantic.txt`, set `EMBEDDING_PROVIDER=local`,
and index with the same command. The default model is
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; first use downloads weights.
Local embeddings do not supply a local evaluator: semantic verdicts still use Gemini.
Without indexed vectors, keyword/exact archive search remains available and the interface
discloses the limitation. No automatic model download or paid call occurs with empty keys.

Live API check on November 19, 2026: `POST /api/v1/verify` for
"The Philippines has 7,641 islands." returned `supported` using Gemini and five
live-search sources in 16.079 seconds. The older configured Flash model timed out;
the default is now `gemini-3.5-flash-lite`. Model explanations exclude inline source
markers; the backend appends IDs from the citation list, and then validates every ID,
quote, and verdict/stance relationship. Failed or invalid assessments still return
insufficient evidence. This smoke check does not establish general accuracy or the
six-second research target. The provider timeout is 20 seconds and the overall
verification deadline remains 25 seconds.

`/demo` now also contains a direct text-checking form using the same production API.
It displays the assessment, provider warnings, and original source links without needing
the extension. The extension is still required for capture on other webpages.

From `backend`, diagnose the actual provider connections without printing credentials:

```powershell
& ..\.venv\Scripts\python.exe -m scripts.check_providers
# Check only evaluation, optionally testing another model without editing .env:
& ..\.venv\Scripts\python.exe -m scripts.check_providers --provider evaluation --model gemini-3.5-flash-lite
```

The diagnostic sends a synthetic model fixture and/or a public search query to the
configured providers, using normal API quotas. It does not run automatically at startup.
Health reports configuration and the selected evaluation model, not an active provider
connectivity guarantee. The HTTP dependency includes SOCKS transport support for proxy
environments. The browser demo was syntax-checked; a real browser launch was unavailable
in the restricted execution environment for this update.

Official references: [Gemini generation](https://ai.google.dev/api/generate-content),
[Gemini embeddings](https://ai.google.dev/api/embeddings),
[Tavily search](https://docs.tavily.com/documentation/api-reference/endpoint/search),
[Chrome activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab),
[offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen).

## Privacy

Only a user action starts processing. After local triage, the text claim goes to the
local backend. Chrome screenshot capture temporarily produces the entire visible viewport
inside the extension; the offscreen document crops the selected region for local OCR.
Neither screenshot nor crop is sent to the backend. The user reviews extracted text before
submission, and recognized text is not logged.

When configured, Tavily receives the claim; Gemini receives the claim and retrieved
excerpts. Cloud embeddings receive archive text during indexing and the claim during
search. No browsing-history collection, cookie access, continuous scanning, or form-value
reading is implemented. A screenshot includes whatever is visibly within its region.
The thesis must describe the temporary full-viewport capture accurately rather than imply
Chrome provides a region-only capture API.

## Tests

```powershell
cd backend
& ..\.venv\Scripts\python.exe -m pytest tests -q
cd ..
node --test tests/extension.test.cjs
```

Backend tests isolate databases and disable real providers. For browser testing:

```powershell
npm install
npx playwright install chromium
# Start the backend on port 8001 in another terminal.
npm run test:browser
```

`UNFAKE_CHROMIUM` may point to Chrome for Testing. The test uses an isolated profile and
Chrome's test-only action trigger to exercise activeTab. `UNFAKE_TEST_OUTPUT` sets the
screenshot directory (default `test-results`). Keep provider keys empty for offline tests.
This does not establish Facebook/TikTok compatibility or cross-browser release readiness.

## Research evaluation

The four-record archive and six-case smoke dataset are development examples. All four
archive records are debunks; expand and independently review the corpus before reporting
accuracy, recall, verdict balance, or generalization.

Use a separately labeled JSONL dataset containing `id`, `claim`, `expected_verifiable`,
optional `expected_verdict`, `relevant_urls`, `input_type`, `language`, and `split`. Preserve
dates and provenance; account for syndicated duplicates. Include English, Filipino,
Taglish, opinions, questions, negation, partial truth, unsupported claims, and current events.

From `backend`:

```powershell
python -m scripts.benchmark DATASET.jsonl --output measurements.json
# --live explicitly enables configured external providers.
python -m scripts.evaluate_ocr OCR_RUNS.jsonl --output ocr-metrics.json
```

OCR rows contain `reference`, `hypothesis`, and `resolution`. Collect multiple resolutions,
zoom factors, fonts, language mixes, contrast levels, and compression conditions.

Confidence calibration needs independently labeled claims separate from final evaluation:

```powershell
python -m scripts.collect_predictions CALIBRATION.jsonl --output data/predictions.jsonl
python -m scripts.calibrate data/predictions.jsonl --model gemini:gemini-3.5-flash-lite --output data/calibration.json
```

The calibration dataset must use `split: "calibration"` and gold `expected_verdict` labels.
The fitter requires at least 30 unique claims and both correct and incorrect predictions;
that minimum is a guard, not proof of statistical sufficiency. Evaluate the mapping on a
held-out set. Model, retrieval, or domain changes require reviewing calibration validity.

The manual-search hypothesis requires a participant study with matched tasks,
counterbalanced order, completion times, independently scored correctness, and usability
measurements. Predeclare the analysis. No participant results or significance are invented.

## Remaining work requiring configuration or research data

- Check the optional local embedding path with downloaded weights. Current local archive
  retrieval is exact/keyword. Repeat representative live cases and real-browser checks;
  the successful API smoke test is not a full end-to-end browser evaluation.
- Expand the fact-check corpus, prepare held-out labels, collect calibration data, run
  OCR studies and the participant comparison. Measurement tools do not replace experiments.
- For large corpora, replace Python's full vector scan with an indexed search strategy.
- Evaluate prompt injection, missing context, source errors, and reasoning hallucinations.
- Confirm third-party license notices before public redistribution of bundled OCR assets.
