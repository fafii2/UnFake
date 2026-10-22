# UnFake API Contract

## Version: v1

Implementation version: 0.4.0. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for provider setup
and privacy. With empty keys, the backend uses reviewed exact archive matches; related
sources alone never establish a verdict. No example citations or placeholder responses remain.

**Base URL:** `http://localhost:8000/api/v1`

---

## Endpoints

### `POST /verify`

Submit a factual claim for evidence-based verification.

#### Request Body

```json
{
  "claim": "string (required, 1–5000 chars)",
  "input_type": "text | image_ocr"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `claim` | `string` | Yes | The factual statement to verify. Whitespace is trimmed. |
| `input_type` | `string` | Yes | How the claim was captured. One of: `text`, `image_ocr`. |

#### Successful Response (200)

Responses also include `warnings` (availability/coverage notices), `timings` (stage
milliseconds), `evaluation_method` (`gemini`, `exact_archive_match`, `insufficient`, or `none`),
and `confidence_kind` (`unavailable` or `calibrated_reliability`). Each evidence item has a
request-scoped `id` such as `S1`; explanation citations refer to those IDs. Source URLs are
validated HTTP/HTTPS URLs. `confidence` is null until a matching empirical calibration
artifact is configured; OCR recognition confidence is a separate client-side value.

```json
{
  "status": "completed",
  "verdict": "supported",
  "explanation": "The claim is supported by...",
  "confidence": null,
  "triage": {
    "is_verifiable": true,
    "reason": "Claim contains a factual assertion."
  },
  "evidence": [
    {
      "title": "Article title",
      "source_url": "https://...",
      "publisher": "Publisher Name",
      "published_date": "2025-01-15",
      "snippet": "Relevant excerpt...",
      "relevance": "supporting",
      "source_type": "local_archive"
    }
  ],
  "original_claim": "The submitted claim text",
  "processing_time_ms": 1250
}
```

#### Status Values

| Status | Meaning |
|---|---|
| `completed` | Full verification pipeline executed successfully. |
| `triage_rejected` | Claim was classified as non-verifiable. |
| `error` | Processing failed. |

#### Verdict Values

| Verdict | Meaning |
|---|---|
| `supported` | Available evidence supports the claim. |
| `contradicted` | Available evidence contradicts the claim. |
| `mixed` | Evidence is conflicting or disputed. |
| `insufficient_evidence` | Not enough evidence found. |
| `null` | Verdict not applicable (e.g., triage rejected). |

#### Evidence Relevance Values

| Relevance | Meaning |
|---|---|
| `supporting` | Evidence supports the claim. |
| `contradicting` | Evidence contradicts the claim. |
| `contextual` | Related but neither supports nor contradicts. |

#### Evidence Source Types

| Type | Meaning |
|---|---|
| `local_archive` | From the local fact-check database. |
| `web_search` | From live web search. |

#### Error Responses

| Code | HTTP | Meaning |
|---|---|---|
| `EMPTY_CLAIM` | 422 | Claim text is empty or whitespace. |
| `CLAIM_TOO_LONG` | 422 | Claim exceeds 5000 characters. |
| `INVALID_INPUT_TYPE` | 422 | Unrecognized input type. |
| `PROCESSING_TIMEOUT` | 504 | Backend took too long. |
| `INTERNAL_ERROR` | 500 | Unexpected server error. |

```json
{
  "status": "error",
  "error_code": "EMPTY_CLAIM",
  "message": "Claim must not be empty or whitespace-only."
}
```

---

### `GET /`

The root route is at `http://localhost:8000/`. The prefixed health route
`GET /api/v1/health` additionally reports booleans for configured live-search/evaluation
providers and the selected embedding provider. It never returns keys.

Health check endpoint.

```json
{
  "service": "unfake-api",
  "version": "0.1.0",
  "status": "running"
}
```

---

## Versioning

All endpoints are prefixed with `/api/v1/`. Breaking changes will use a new version prefix.

## CORS

The backend allows requests from:
- Chrome extension origins (`chrome-extension://<id>`)
- `http://localhost:3000` (development)

## Rate Limits

No rate limiting in Milestone 1. Will be added as needed.
