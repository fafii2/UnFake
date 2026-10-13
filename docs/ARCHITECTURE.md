# UnFake — Architecture

## System Overview

UnFake is a two-part system:

1. **Browser Extension** (client) — Manifest V3 Chrome extension
2. **FastAPI Backend** (server) — Python REST API

They communicate over HTTP (`POST /api/v1/verify`).

## Component Map

```
┌─────────────────────────────────────────────────────────────┐
│  BROWSER EXTENSION (Manifest V3)                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Popup       │  │  Content     │  │  Background       │  │
│  │  (popup.html) │  │  Script      │  │  Service Worker   │  │
│  │              │  │  (content.js)│  │  (service-worker) │  │
│  │  - Status    │  │  - Text sel  │  │  - Context menu   │  │
│  │  - Manual    │  │  - Modal UI  │  │  - API calls      │  │
│  │    input     │  │  - Results   │  │  - Message hub    │  │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬────────┘  │
│         │                  │                     │           │
│         └──── chrome.runtime.sendMessage ────────┘           │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP POST
                                ▼
┌─────────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND                                            │
│                                                             │
│  ┌────────────┐   ┌──────────────────────────────────────┐  │
│  │  API Router │──▶│  Services                            │  │
│  │  /api/v1/   │   │                                      │  │
│  │  verify     │   │  ┌──────────────┐ ┌──────────────┐  │  │
│  │             │   │  │ Preprocessor │ │ Triage Engine│  │  │
│  └────────────┘   │  └──────┬───────┘ └──────┬───────┘  │  │
│                    │         │                 │          │  │
│                    │         ▼                 ▼          │  │
│                    │  ┌──────────────┐ ┌──────────────┐  │  │
│                    │  │  Retrieval   │ │  Evaluator   │  │  │
│                    │  │  Service     │ │  (RAG)       │  │  │
│                    │  └──────┬───────┘ └──────────────┘  │  │
│                    └─────────┼────────────────────────────┘  │
│                              │                               │
│                    ┌─────────┼────────────┐                  │
│                    │         ▼            │                  │
│                    │  ┌──────────┐  ┌────────────┐          │
│                    │  │  SQLite  │  │ Web Search │          │
│                    │  │ + Vector │  │  Provider  │          │
│                    │  └──────────┘  └────────────┘          │
│                    │     Data Layer                │          │
│                    └──────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. User selects text → content script captures it
2. Content script → service worker via `chrome.runtime.sendMessage`
3. Service worker → `POST /api/v1/verify` via `fetch`
4. Backend preprocesses → triages → retrieves → evaluates
5. Backend returns JSON response
6. Service worker → content script with result
7. Content script renders the modal on the page

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Manifest V3** | Required for new Chrome extensions. Uses service workers instead of persistent background pages. |
| **FastAPI** | Lightweight, async-ready, automatic OpenAPI docs, Pydantic validation. |
| **SQLite** | Simple, serverless, file-based. Suitable for an academic project's local fact-check archive. |
| **All CSS prefixed `unfake-`** | Prevents style collisions when injecting into arbitrary webpages. |
| **Stub-first approach** | Proves end-to-end communication before building real verification logic. |

## File Structure

See [README.md](../README.md) for the full directory listing.
