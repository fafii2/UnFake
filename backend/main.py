"""
UnFake Backend — FastAPI Application Entry Point

Start the server:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
import logging
from fastapi.middleware.cors import CORSMiddleware

from config import settings, BASE_DIR
from api.router import router as api_router

app = FastAPI(
    title="UnFake API",
    description="AI-assisted misinformation verification backend",
    version="0.4.0",
)

# CORS middleware — allows the browser extension to reach the backend.
# In development, we also allow localhost origins for testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Mount the API router under /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0]
    code = 'INVALID_REQUEST'
    if 'input_type' in first['loc']:
        code = 'INVALID_INPUT_TYPE'
    elif first['type'] == 'string_too_long':
        code = 'CLAIM_TOO_LONG'
    elif 'claim' in first['loc']:
        code = 'EMPTY_CLAIM' if first['type'] in {'missing', 'string_too_short', 'value_error'} else 'INVALID_CLAIM'
    return JSONResponse(status_code=422, content={'status': 'error', 'error_code': code,
                         'message': '; '.join(str(error['msg']) for error in errors)})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    code = {504: 'PROCESSING_TIMEOUT', 422: 'INVALID_CLAIM'}.get(exc.status_code, 'REQUEST_ERROR')
    return JSONResponse(status_code=exc.status_code, content={'status': 'error', 'error_code': code, 'message': str(exc.detail)})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    # Do not log claim contents, provider bodies, or API keys.
    logging.getLogger('unfake').error('Unhandled verification error: %s', type(exc).__name__)
    return JSONResponse(status_code=500, content={'status': 'error', 'error_code': 'INTERNAL_ERROR',
                         'message': 'Verification could not be completed. Please try again.'})


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"service": "unfake-api", "version": "0.4.0", "status": "running"}


@app.get('/demo', include_in_schema=False)
async def demo():
    return FileResponse(BASE_DIR / 'web' / 'demo.html')
