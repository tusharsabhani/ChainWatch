# ChainWatch Frontend

The frontend is a standalone `Next.js` App Router project for the ChainWatch UI.

Phase 1 now follows the approved `stitch_chainwatch_mocks` visual system: a dark operational desktop rail, a compact light workspace, and route-shaped page shells that mirror the mock exports.
Phase 2 now adds live Dashboard, Map, and Product Detail pages on top of that shell, while Chat, Reports, and Import workflows remain for later phases.
Phase 3 now completes those workflow surfaces with live chat, report generation, and local-path import actions through same-origin frontend route handlers.

Current frontend stack:

- `Next.js`
- `React`
- `TypeScript`
- `Tailwind CSS`
- `React Simple Maps`
- local UI components from this repository

## Requirements

- `Node.js 20+`
- `npm` or another package manager that can install from `package.json`

## Setup

From the repository root:

```bash
cd frontend
npm install
```

If your backend is running somewhere other than `http://127.0.0.1:8000/api`, create `.env.local` from `.env.example` and change `NEXT_PUBLIC_API_BASE_URL`.

## Run

From the `frontend/` directory:

```bash
npm run dev
```

The app will be available at `http://127.0.0.1:3000`.

## Phase 1 Scope

Phase 1 implements:

- the global app shell
- mock-shaped route layouts for all v1 pages
- shared theme tokens, typography, spacing, and severity colors
- the shared API client
- common loading, error, empty, retry, and freshness UI

The Settings page now includes live import actions, and the Chat and Reports pages now run real workflow interactions while still using the approved visual system. The current Reports page is generation-only and does not yet include in-product report browsing or Markdown preview.

For the best first run:

- seed backend demo data with `uv run python -m app.seed` in `backend/`
- start the backend before opening the frontend
- expect external-risk sections to be limited unless live search is configured or cached external-risk data already exists locally
