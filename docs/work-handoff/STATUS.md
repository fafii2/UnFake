# UnFake project status

## Phase 2 design checkpoint

Date: 2026-11-05. Development branch: `feat/unfake-backend`. Previous Phase 1 audit: `c501537`. This documentation commit is the Phase 2 checkpoint. The finalized planning is in [ARCHITECTURE.md](ARCHITECTURE.md) and [SOURCES.md](SOURCES.md). The review used the existing code, source-cited notebook answers, and public provider documentation. The checkpoint contains documentation changes.

The design preserves the loopback FastAPI API, local SQLite evidence storage, and both Chromium MV3 input paths. The UnFake notebook cross-check confirmed the local OCR and evidence-store baseline. It cites SRS section 3.1.1 for Credible, Questionable, and Contradicted, and FR-07 for a percentage confidence score. FR-03 and FR-04 describe a direct OCR-to-cleaning path. The editable review in the current build needs a team decision before Phase 7. The plan keeps v1 machine values and marks the SRS display mapping as provisional. Confidence stays unavailable through Phase 3 and until Phase 5 calibration is validated. The notebook calls for classical supervised ML, with final verdicts gated by evidence.

The initial evidence archive uses reviewed VERA Files and Tsek.ph records. PSA OpenSTAT and BSP are scoped primary sources. Tavily is a conditional discovery adapter after a privacy, terms, and quota check. A local classical model requires a real labeled corpus and an agreed prediction target. Google Fact Check Tools and Gemini remain optional research comparisons. Supabase is optional for a shared curated archive. Chrome redirected to sign-in, so project inventory and available account quotas remain unverified.

### Phase 3 readiness

Phase 3 can begin with offline foundation work. The Windows install and Chrome loopback demo remain acceptance checks. Provider credentials, Supabase access, final display definitions, and the OCR review decision are later integration or release gates.

- Reproduce the pinned backend install and tests on a host with package access. Confirm the bundled sample verdict and links in Chrome over the real loopback API. The previous host session could not resolve PyPI.
- Preserve the current contract. Verify the original SRS wording for display labels, short selections, editable OCR, and Shadow DOM before changing the extension. Record approval for any search-provider substitution. Confirm the classifier target before dataset labeling.
- Establish the reviewed evidence import policy and provenance fields. Live search and any shared database depend on source rights, data-handling review, and account-specific checks.

## Phase 1 checkpoint

Audit date: 2026-11-05 (Philippines). Antigravity opened the existing `fafii2/UnFake` workspace on a clean `master` at `dd1e095d51de659a5c4a7dbe36a32fadb6bd352e` (v0.4.0), matching the local `origin/master` reference. The audit uses `feat/unfake-backend`. The checkout was reused. This checkpoint covers documentation.

### Verified during Phase 1

- Reviewed the source-cited UnFake notebook audit in Gemini desktop. The paper and SRS describe Chromium MV3, explicit text selection, viewport cropping, local OCR, and sourced verification results.
- Inspected the extension and existing FastAPI backend. See [BASELINE.md](BASELINE.md) for the code paths, test evidence, and differences from the SRS.
- `npm test` passed 8 tests. Python compilation, syntax checks for eight first-party extension scripts, and checks for the five manifest entry paths passed. The unpacked extension is the checked-in `extension/` directory and has no separate bundle step.

### Chrome and backend follow-up

- Enabled Developer Mode with user confirmation and loaded the repository's unpacked `extension/` directory in Chrome. Chrome enabled UnFake v0.4.0.
- Tested the highlighted-text context menu on a public VERA Files fact-check, the toolbar popup, client-side opinion triage, and viewport cropping with local OCR. OCR produced editable text and reported 95% recognition confidence for one crop.
- The browser showed a backend-unreachable error after factual text and reviewed OCR submissions. Chrome's extension diagnostics recorded `TypeError: Failed to fetch` in the service worker. The popup's archived example populated its input.
- An isolated in-process FastAPI smoke check with cached dependencies passed health, demo, exact archive verification with a VERA Files source, insufficient evidence, and opinion triage. The smoke environment used newer cached versions of FastAPI, Uvicorn, and Pydantic than the project pins. It used a temporary SQLite database with external providers disabled.
- A loopback-only server reported successful startup using the same cached packages with a temporary audit event loop. Chrome still could not reach it. The pinned install failed at DNS resolution, so the full backend suite and browser-to-backend verification remain open.
- Antigravity published the audit branch. Firefox remains deferred. Chrome was sufficient for the client-side baseline.

### Remaining Phase 1 verification

Run the pinned backend suite in a host environment with package access. Start FastAPI on loopback port 8000, then confirm the archived verdict and clickable evidence in Chrome through both highlighted text and reviewed OCR. Reconcile editable OCR review, modal isolation, input validation, and the live search provider with the SRS. Live provider validation and a reviewed research corpus remain open. The current-state audit was completed. The bundled demo remains unverified from Chrome.
