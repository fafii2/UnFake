# Archive provenance

`archive.json` is a **four-record starter corpus**, not a representative research dataset.
Records contain short original paraphrases of publicly accessible fact-checks verified on
2026-10-22, publication dates, publisher ratings, and canonical links. Copyright remains
with the publishers; no full articles are distributed. Reviewed aliases are translations
of the same assertion, never approximate search matches. Tsek.ph syndicated sources point
to their original publisher to avoid counting one article as independent corroboration.

The dated earthquake example represents a false *forecast*, not proof that no earthquake
could occur. Old assistance claims must never establish the availability of current aid.
Records should be expanded, independently reviewed, and split from held-out evaluation
claims before thesis measurements. All four starter records are debunks; this corpus
cannot establish verdict-class balance, model quality, or confidence calibration.

Import any validated JSON array in this format with `python -m scripts.seed_archive FILE`.
Use `--embed` to index vectors with the configured embedding adapter. The vector model
identifier is stored alongside each embedding; changing models requires reindexing.
No model download or paid API call occurs just by starting the unconfigured backend.
