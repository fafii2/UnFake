# UnFake v0.4.0 baseline

Source revision `dd1e095d51de659a5c4a7dbe36a32fadb6bd352e`. The requirements comparison uses the Gemini UnFake notebook's cited audit of `UnFake.pdf` and the Software Requirements Specification. Source findings below refer to this checkout.

## Extension and backend

| Area | Finding from source |
| --- | --- |
| Packaging | Vanilla JavaScript, HTML, and CSS in `extension/`. Manifest V3 declares a service worker, toolbar popup, and `activeTab`, `contextMenus`, `offscreen`, `scripting`, and `tabs` permissions. Its only declared host permission is `http://localhost:8000/*`. The extension CSP allows local WASM execution. |
| Highlighted text | `extension/background/service-worker.js` receives `info.selectionText` from the context menu, trims it, and invokes the verification path. Manual entry in the popup and reviewed OCR use the same path. `extension/shared/claims.js` normalizes and triages claims locally. Factual input is posted to `/api/v1/verify`. |
| Screenshot and OCR | The crop canvas in `extension/content/image-crop.js` supplies the selected bounds. The worker verifies the active tab, removes overlays, and captures the viewport. `extension/offscreen/offscreen.js` crops the image and performs real recognition using bundled English Tesseract.js/WASM assets. The in-page modal displays a preview and editable recognized text. Only the reviewed claim text is submitted to the backend. |
| Interface and errors | The popup queries `/api/v1/health`. The injected in-page interface has loading, triage, OCR review, result, and failure views. Results include verdict, explanation, evidence links, and notices. Verdict reliability is displayed only when the API supplies calibrated confidence. OCR recognition confidence is separate. The worker has timeout and stale-response handling. |
| Demo data | The popup's archived example button inserts a fixed claim. `backend/web/demo.html` also includes a fixed sample and quote card. The four starter archive records are sourced debunks. Verification uses backend retrieval and reviewed exact-claim ratings in offline mode. Other claims can return insufficient evidence. The popup fixture does not supply a verdict. |
| Backend | `backend/main.py` mounts FastAPI routes under `/api/v1`. `backend/api/router.py` repeats claim validation and triage. The pipeline includes SQLite FTS5, reviewed imports, optional model-tagged embeddings, Tavily live retrieval, Gemini structured stance evaluation with citation checks, and optional confidence calibration. |
| Compatibility | The Chromium-specific offscreen document and capture APIs matter in addition to MV3 syntax. Chrome and Edge are the intended test targets. Firefox was deferred and has no compatibility result from this audit. |

## Differences and open work

- The SRS baseline describes client validation for selections of at least three words. Current rule triage generally requires four words and accepts a three-word clause with a recognized copula.
- The SRS describes OCR flowing directly to cleaning and a Shadow DOM modal. The checkout asks the user to review or edit OCR text and appends modal elements directly to the page DOM. Bundled OCR assets are English-only. The text triage rules cover English, Filipino, and Taglish.
- The SRS cited a local `/api/verify` endpoint and DuckDuckGo retrieval. The current extension and backend agree on `/api/v1/verify` and the live search adapter uses Tavily. SQLite archive retrieval works without provider configuration in the implemented design.
- The checkout has the local endpoint and optional provider integrations. Live provider runs, embedding index setup, broader archive coverage, independent labels, and empirical confidence calibration still need verification or research data. A classical supervised verification classifier was not found in the checkout.

## Checks performed

| Check | Session result |
| --- | --- |
| Extension unit tests | `npm test` passed all eight tests on Node 25.6.1. Coverage includes triage, tab routing, stale results, repeat injection, and mocked capture ordering. |
| Static packaging and syntax | Manifest JSON parsed, five declared entry paths exist, eight first-party JavaScript files passed `node --check`, and the backend passed Python 3.11.9 bytecode compilation. No build script is declared. |
| Backend runtime and tests | The pinned install failed with `[Errno 11001] getaddrinfo failed`. A separate in-process ASGI smoke test passed health, demo, archived verdict with evidence, insufficient evidence, and opinion triage with cached FastAPI 0.133.1, Uvicorn 0.41.0, Pydantic 2.12.5, and HTTPX 0.28.1. The archived example returned `contradicted`, `exact_archive_match`, a VERA Files URL, and null calibrated confidence. The full pytest suite was not run. |
| Chrome installation | Chrome loaded and enabled the unpacked MV3 extension from `extension/`. The toolbar popup opened and showed `Backend unreachable`. Its archived example filled the claim field and enabled the Verify button. |
| Chrome highlighted text | Selecting the lead of a [VERA Files fact-check](https://verafiles.org/articles/vera-files-fact-check-no-tons-of-tallano-gold-allegedly-owned-by-marcoses-in-bsp-storage) exposed the UnFake context menu. The action showed the loading dialog and then a backend-unreachable error. Escape dismissed the result. |
| Chrome crop and OCR | The popup opened the crop overlay. A viewport crop of the article headline produced editable text with 95% OCR recognition confidence. OCR omitted the word “of” from “No tons of.” Submitting the recognized text showed the backend-unreachable result. |
| Chrome triage | A controlled opinion entered through the popup rendered `Not a Factual Claim` and explained why it was not submitted. |
| Chrome diagnostics and remaining gap | The extension error view showed `[UnFake] API call failed: TypeError: Failed to fetch` in `background/service-worker.js`. Chrome could not reach the health URL after the temporary server reported listening on IPv4 loopback. The browser did not render a sourced verdict or evidence links in this run. Chrome covered the browser-side baseline. Edge was unnecessary and Firefox remained deferred. |
