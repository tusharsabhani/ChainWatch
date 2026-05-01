# ChainWatch Backend

The backend is an isolated FastAPI project for the ChainWatch local-first runtime.

## Requirements

- `uv`
- Python `3.12`

## Setup

From the repository root:

```bash
cd backend
uv sync --extra dev
```

## Run

From the `backend/` directory:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## First Endpoint

- `GET /api/health`

This endpoint verifies runtime readiness, sqlite connectivity, managed storage paths, and provider configuration flags.

## Test

From the `backend/` directory:

```bash
uv run pytest
```

