# Rowentrix Lead Generator — hosted on Vercel

UK B2B lead generator: search by city/category, detect missing websites,
scan for existing AI chatbot/voice-agent tools, score leads, browse in a
Vite + React + TypeScript + Tailwind UI, export to CSV. Backend is
FastAPI + LangGraph, hosted as Vercel serverless functions; data lives in
Postgres (Supabase). Vercel builds the frontend and the Python API together
from one repo.

## Why this stack, not SQLite + a plain script

Vercel functions are stateless and ephemeral — nothing written to disk during
one request survives to the next, and there's a hard execution timeout
(10s on the free/Hobby plan, 60s on Pro). That ruled out SQLite (no
persistent disk) and forced the AI-tool website scan to run **concurrently**
across leads instead of one at a time (see `detection/ai_tool_detector.py`).
Playwright/JS-rendering was dropped entirely for the hosted version — too
heavy for a serverless bundle and too slow to fit the timeout. If you want
that deeper JS-widget scan, run the original CLI locally instead (still in
this repo as `main.py`).

## 1. Set up Postgres (Supabase)

1. Create a free project at supabase.com
2. Project → Settings → Database → Connection string → copy the URI
   (use "Session pooler" mode — works better with serverless functions
   than the direct connection)
3. Keep this string handy, you'll paste it in twice (local `.env` + Vercel)

## 2. Business data source: OpenStreetMap (no signup needed)

Business search now uses OpenStreetMap (Nominatim for geocoding + Overpass
for the actual business search) instead of Google Places — free forever, no
API key, no billing account. The trade-off: OSM data is community-mapped,
so coverage varies by area, and categories have to match a tag mapping in
`lead_generator/sources/osm_places.py` (`CATEGORY_TAGS`) — if you search a
category that isn't in that dict yet, add it there first.

## 3. Push to GitHub

```bash
git init
git add .
git commit -m "Initial lead generator"
gh repo create rowentrix-lead-generator --private --source=. --push
# or: create the repo on github.com, then git remote add origin <url> && git push
```

`.env` is already in `.gitignore` — never commit real keys.

## 4. Deploy on Vercel

1. vercel.com → New Project → import your GitHub repo
2. Vercel reads `vercel.json`: it runs `npm run build` for the Vite frontend
   (output to `dist/`) and picks up `api/index.py` as a Python serverless
   function automatically — no extra config needed beyond env vars
3. Add environment variables (Project → Settings → Environment Variables):
   - `DATABASE_URL`
   - `USE_LLM_SCORING` (optional, default false)
   - `OPENAI_API_KEY` (only if USE_LLM_SCORING=true)
4. Deploy. Vercel gives you a live URL — the form at `/` calls `/api/generate`.

Every future `git push` to your main branch auto-redeploys.

## 5. Test it

Open your Vercel URL, enter a city + category, hit "Find Leads." Or hit the
API directly:

```bash
curl -X POST https://your-app.vercel.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{"city":"Birmingham","category":"care home","max_results":10,"no_website_only":true}'
```

CSV export: `GET /api/export` (downloads everything currently in the DB
above a score threshold, `?min_score=4`).

## Local development

You need two terminals — one for the Python API, one for the Vite frontend.

```bash
# Terminal 1 — backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL
uvicorn api.index:app --reload --port 8000

# Terminal 2 — frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173). Vite's dev server
proxies `/api/*` requests to the FastAPI server on port 8000 (see
`vite.config.ts`) so there's no CORS setup needed locally.

Or run the original CLI (no server, writes straight to Postgres):

```bash
python main.py --city "Birmingham" --category "care home" --max-results 10 --no-website-only
```

## Project layout

```
src/
  App.tsx                 # the "Find Leads" UI — form, results table, CSV export link
  main.tsx, types.ts, index.css
index.html                 # Vite entry point
package.json, vite.config.ts, tailwind.config.js, tsconfig.json
api/
  index.py                 # FastAPI app — Vercel's entrypoint, wraps the pipeline
lead_generator/
  config.py               # env var loading
  db.py                   # Postgres schema + read/write
  sources/google_places.py
  detection/
    signatures.py         # known chatbot/AI-voice vendor fingerprints — maintain this over time
    website_detector.py   # FOUND / NOT_FOUND / UNCERTAIN
    ai_tool_detector.py   # concurrent scan across leads
  scoring/lead_scorer.py  # rule-based, no LLM needed
  graph/
    state.py              # LangGraph state object
    pipeline.py            # the actual graph — start here to understand flow
  export/csv_export.py
main.py                   # local CLI, still works, uses the same package
vercel.json
requirements.txt
```

## Known limitations, honestly

- **Free-tier 10s timeout is tight.** With `max_results` above ~10-15,
  the concurrent website scan may not finish in time on Hobby. Either keep
  requests small, or upgrade to Pro (60s) — `vercel.json` already requests
  `maxDuration: 60`, which only takes effect on plans that allow it.
- **AI voice-agent detection is website-only**, same caveat as before —
  it can't see phone-only AI receptionists with no web widget.
- **No JS-rendered widget detection** on the hosted version (Playwright
  removed). A chatbot that only loads via JavaScript after page load will
  be missed. Use the local CLI with a from-scratch Playwright add-on if you
  need that depth.
- **`signatures.py` goes stale** — new vendors launch constantly, it's a
  file you maintain, not a one-time download.
