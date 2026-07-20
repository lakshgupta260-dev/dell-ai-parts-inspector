# Dell Parts Inspector — Frontend

React + Vite frontend for the `dell-ai-parts-inspector` backend. Every page is
wired to the real FastAPI endpoints — this is not a mockup. Point it at a running
backend and it works.

## Run it

You need Node.js (LTS, from nodejs.org). Then:

```bash
cd frontend
npm install
cp .env.example .env      # edit if your backend isn't on localhost:8000
npm run dev
```

Open the URL it prints (http://localhost:5173). Register an account, then sign in.

**The backend must be running** at the URL in `.env` (default `http://localhost:8000`).
Start it first:

```bash
cd backend
uvicorn app.main:app --reload
```

## The five pages

| Page | Route | Backend endpoints used |
|---|---|---|
| Login / Register | `/login` | `POST /api/v1/auth/login`, `/register` |
| Dashboard | `/` | `GET /api/v1/history/analytics`, `GET /api/v1/history` |
| New Inspection | `/new` | `POST /api/v1/upload/inspection`, `POST /api/v1/pipeline/run/{id}` |
| Inspection Detail | `/inspection/:id` | `GET /api/v1/history/{id}`, `GET /api/v1/report/download/{id}`, `POST /api/v1/notify/*` |
| History | `/history` | `GET /api/v1/history` |

## How it maps to the backend

Everything that talks to the API lives in **`src/lib/api.js`**. Each function is a
thin wrapper over one real endpoint, with the exact request/response shape from
the backend's Pydantic models. If the backend changes a route or a field, this is
the one file you edit.

Key contract details already handled:

- **Auth**: login takes `{username, password}`, register takes
  `{username, email, password, role}` where role is `INSPECTOR` or `QA_MANAGER`.
  The returned `access_token` is stored in localStorage and attached as
  `Authorization: Bearer <token>` on every request (see the axios interceptor).
- **Upload**: sends multipart form fields named exactly `front_image` and
  `back_image`, as the `/upload/inspection` endpoint expects.
- **Pipeline**: the New Inspection wizard uploads, gets the `inspection_id`, then
  calls `/pipeline/run/{id}` which runs all 5 stages server-side. The result card
  reads `fraud_score`, `verdict`, `service_tag`, `model_name`, and the per-stage
  `*_status` fields.
- **Verdicts**: the UI uses the backend's exact vocabulary —
  `AUTHENTIC` (green), `SUSPICIOUS` (amber), `COUNTERFEIT` (red).
- **Fraud score** colouring: 0–33 green, 34–66 amber, 67–100 red.
- **PDF**: the detail page's "Download PDF" opens
  `GET /api/v1/report/download/{id}` in a new tab.
- **Notifications**: the detail page can POST a phone number to
  `/notify/whatsapp/{id}` or `/notify/vapi/{id}`.

## Structure

```
src/
  lib/
    api.js        ← ALL backend calls. The integration surface.
    auth.jsx      ← auth context, design tokens, verdict/score colour helpers
  components/
    ui.jsx        ← buttons, panels, score dial, radar, animated background
    Shell.jsx     ← top nav + layout for authenticated pages
  pages/
    Login.jsx  Dashboard.jsx  NewInspection.jsx  InspectionDetail.jsx  History.jsx
  App.jsx         ← routing + protected routes
  main.jsx        ← entry point
```

## Design

Industrial inspection-instrument aesthetic on Dell blue (`#0f7dc2`): dark slate
console, monospace for all data/metrics like a real readout, animated scan-grid
background with a slow blue sweep line. Verdict tags and the score dial are the
signature elements. Respects `prefers-reduced-motion`.

## Merging into the team repo

The team repo already has a `frontend/` folder scaffolded with Vite. Replace its
`src/`, `index.html`, `package.json`, and `vite.config.js` with these files (the
scaffold was set up for TypeScript/vanilla; this is React JSX, which is what the
project needs). Keep their `tailwind.config.js` if you later want Tailwind — this
build uses inline styles and needs no Tailwind, so it runs either way.

Then:
```bash
cd frontend
npm install
npm run dev
```
