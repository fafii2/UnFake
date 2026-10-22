# Bundled OCR assets

The following upstream assets were already included in the repository. Their identity
was checked on 2026-10-22 against the listed distribution URLs. JavaScript files match
after line-ending normalization; the trained-data archive matches byte for byte.

| Local file under extension/lib | Distribution |
|---|---|
| tesseract.min.js | https://cdn.jsdelivr.net/npm/tesseract.js@7.0.0/dist/tesseract.min.js |
| worker.min.js | https://cdn.jsdelivr.net/npm/tesseract.js@7.0.0/dist/worker.min.js |
| tesseract-core-lstm.wasm.js | https://cdn.jsdelivr.net/npm/tesseract.js-core@7.0.0/tesseract-core-lstm.wasm.js |
| tessdata/eng.traineddata.gz | https://tessdata.projectnaptha.com/4.0.0/eng.traineddata.gz |

Tesseract.js and Tesseract.js-core use Apache License 2.0. License texts and bundled
JavaScript dependency notices are retained beside these files as
`TESSERACT-LICENSE.txt`, `TESSERACT-CORE-LICENSE.txt`,
`tesseract.min.js.LICENSE.txt`, and `worker.min.js.LICENSE.txt`.
Upstream projects: https://github.com/naptha/tesseract.js,
https://github.com/naptha/tesseract.js-core, and https://github.com/tesseract-ocr/tessdata.

The English trained-data file's local SHA-256 is
`ed350f3752f81ee8f38769edc14d92d997dababe23b565c59879372cc46a2468`.
Retain the upstream trained-data licensing information when redistributing it.

Fact-check metadata and short original paraphrases in `backend/data/archive.json`
retain publisher attribution and links. They are not a redistribution of full articles.
See `backend/data/README.md` for provenance and dataset limitations.

These notices do not assign a license to the UnFake project's original application code;
the upstream repository does not currently contain a project-wide LICENSE file.
