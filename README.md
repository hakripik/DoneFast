# Study Assistant

A study assistant for course PDFs: upload lecture notes, textbook chapters, or
assignment sheets, ask a question, and get an answer that's grounded in the
material, checked against its own sources, scored for confidence, and — on
request — written back onto a copy of the source PDF as sticky-note
annotations plus an appended answer sheet.

It's a small, from-scratch RAG pipeline with an agentic verification step
layered on top, built to demonstrate the whole stack: chunking and retrieval,
structured LLM calls, a solver → verifier → reflection loop, a hand-built
(not trained) confidence score, and PDF manipulation — not just a thin
wrapper around a chat endpoint.

## How it works

```
PDF upload
  │
  ▼
Ingestion        PyMuPDF extracts text per page, detects headings via font-size
                 deltas, and splits into ~300–600 word chunks on sentence
                 boundaries, tagged with document/page/heading metadata.
  │
  ▼
Retrieval        Chunks are embedded locally (sentence-transformers,
                 all-MiniLM-L6-v2) and stored in a persistent ChromaDB
                 collection. A question is embedded the same way and matched
                 by cosine similarity.
  │
  ▼
Solver           Claude (claude-haiku-4-5) answers using only the retrieved
                 chunks as context, explicitly instructed to say "I don't
                 know" rather than guess, and to cite which chunks it used.
  │
  ▼
Verifier         A separate Claude call — not the solver re-checking its own
                 work — judges whether the answer is actually supported by
                 the retrieved evidence, and lists specific unsupported
                 claims if not.
  │
  ▼
Reflection       If the verifier flags a real problem, this step proposes a
                 rephrased search query and triggers exactly one retry of
                 retrieval + solve + verify. Capped at one retry so a bad
                 case can't loop or run up API cost.
  │
  ▼
Confidence       A deterministic formula (no LLM call) combines retrieval
                 similarity, the verifier's outcome, and whether a retry was
                 needed into a 0–100 score with a plain-language breakdown of
                 why.
  │
  ▼
Export           On request, PyMuPDF opens the original PDF read-only, drops
                 a sticky-note annotation on each cited page, and appends a
                 summary page with the question, answer, confidence, and full
                 citation list. Saved as a new file — the original is never
                 modified.
```

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI |
| PDF parsing & annotation | PyMuPDF (`fitz`) |
| Embeddings | `sentence-transformers` (local, `all-MiniLM-L6-v2`) — swappable for an API-based embedder later without touching call sites, since it's isolated behind one `embed()` function |
| Vector store | ChromaDB, local persistent client (no external service) |
| LLM | Anthropic Claude API (`anthropic` SDK), `claude-haiku-4-5` |
| Frontend | React + Vite + Tailwind CSS v4 |
| Containers | Docker + Docker Compose |

## Running it

You'll need an Anthropic API key either way — get one at
[console.anthropic.com](https://console.anthropic.com) (Settings → API Keys).

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
# edit backend/.env and set ANTHROPIC_API_KEY=sk-ant-...

docker compose up --build
```

Open `http://localhost:5173`. The frontend container serves the built app via
nginx, which reverse-proxies `/api/*` to the backend container over the
Docker network — the browser never talks to the backend directly, so there's
no CORS to think about in this path.

Uploaded PDFs, the ChromaDB index, and annotated exports are bind-mounted to
`backend/uploads/`, `backend/chroma_db/`, and `backend/annotated/` on the
host, so they survive `docker compose down` / `up` — only removing those
folders (or running the app's own "Clear library" action) resets them.

### Option B — Run it manually

Backend:

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
uvicorn app.main:app --reload
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

> **macOS + Homebrew note:** on some macOS/Homebrew combinations,
> `python@3.11`'s bundled `pyexpat` module fails to import due to a symbol
> mismatch against the system `libexpat`. If `pip install` or `python` itself
> errors on import with an `expat` symbol error, the fix is
> `export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib:$DYLD_LIBRARY_PATH"`
> before running Python (the committed `venv/bin/activate`, once created,
> already does this for you).

## Project structure

```
backend/
  app/
    main.py           # FastAPI app + routes
    models.py          # pydantic request/response schemas
    ingestion/           # PDF parsing (parser.py) + chunking (chunker.py)
    retrieval/             # embeddings (embedder.py) + ChromaDB store (store.py)
    agents/                   # solver.py, verifier.py, reflection.py, confidence.py,
                               # orchestrator.py (ties them together), errors.py
    annotation/                 # annotator.py — PDF sticky notes + summary page
  requirements.txt
  .env.example
  Dockerfile
frontend/
  src/
    components/        # Header, Library, AskPanel, ResultPanel, ConfidenceStamp,
                        # CitationChips, ErrorBanner
    lib/api.js          # all backend fetch calls, centralized
  Dockerfile
  nginx.conf            # static file serving + /api/* proxy, used in the Docker image
docker-compose.yml
```

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `POST /upload` | Upload one or more PDFs — parses, chunks, embeds, indexes |
| `GET /search?query=&top_k=` | Raw similarity search (no LLM call) — mostly a debugging/testing endpoint at this point, not used by the polished UI |
| `POST /ask` | `{question, top_k}` → runs the full solver/verifier/reflection/confidence pipeline |
| `POST /export` | `{document_name, question, answer, confidence, confidence_breakdown, citations}` → annotated PDF download |
| `DELETE /clear` | Deletes all uploaded PDFs and clears the vector store |

## Known limitations

Being upfront about what this is and isn't:

- **Heading detection is a heuristic**, not a layout parser — it treats any
  line with a notably larger font size than the page's dominant size as a
  heading. It works well on lecture-slide and textbook-style PDFs; it can
  misfire on unusual formatting (multi-column layouts, decorative title
  pages).
- **Confidence scoring is a hand-tuned formula, not a trained or calibrated
  model.** The point-weighting and thresholds (e.g. what counts as a "weak"
  retrieval match) were picked by testing against a handful of real
  questions, not validated at scale. It's explainable in one sentence, which
  was the design goal, but it isn't statistically rigorous.
- **The reflection loop retries exactly once.** If the first retrieval pass
  is bad in a way one rephrased query can't fix, the answer that comes back
  is the best of two attempts, not a guaranteed-good one.
- **No document library persistence across page loads.** The backend's
  ChromaDB index and `uploads/` folder persist fine across restarts, but
  there's no "list existing documents" endpoint, so the frontend's Library
  panel only shows what's been uploaded in the current browser session — even
  though asking questions still searches everything indexed previously.
- **Single shared collection, no auth, no multi-user isolation.** This is
  built for one person's personal document set running locally, not a
  multi-tenant deployment.
- **Sticky-note annotations land at a fixed point** (the page's top-left
  margin), not next to the actual cited passage — PyMuPDF doesn't give an
  easy way to locate specific text on a page from a chunk of extracted text
  alone.
- **No automated test suite.** This was built interactively, phase by phase,
  with manual verification (including real API calls and real PDFs) at each
  step rather than a CI-backed test suite.

## What I'd do differently / next

Swap the embedding model behind an API-based one for better retrieval quality
on tricky documents; add a real "list uploaded documents" endpoint so the
Library panel reflects what's actually indexed rather than just the current
session; and replace the confidence formula's hand-picked weights with values
tuned against a labeled set of question/answer pairs instead of eyeballed
test cases.
