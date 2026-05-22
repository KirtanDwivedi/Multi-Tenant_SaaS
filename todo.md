# Multi-Tenant Project — Future Reference

Saved from prior chats: how to run the stack, and how Gemini / GitHub / RAG / prompts fit together.

---

## Chat 1 — How to run server & client

Your venv in `server/` is still fine. Use these steps each time:

### Server

```powershell
cd "E:\Visual Studio Code\Projects\Capstone Project\multi_tenate\server"
.\venv\Scripts\activate
pip install -r requirements.txt
pip install "starlette>=0.36.3,<0.37.0"
python main.py
```

Uvicorn runs on **http://0.0.0.0:8000**.

**Health check:** http://localhost:8000

```json
{
  "status": "running",
  "gemini_configured": false,
  "vector_backend": "json",
  "collection": "tenant_knowledge"
}
```

(`gemini_configured` becomes `true` after you set a real key in `.env`.)

### Client (separate terminal)

```powershell
cd "E:\Visual Studio Code\Projects\Capstone Project\multi_tenate\client"
npm run dev
```

Open **http://localhost:5173**.

### Environment (`server/.env`)

```env
GEMINI_API_KEY=YOUR_API_KEY
VECTOR_STORE=json
```

Replace `YOUR_API_KEY` with your real Google Gemini key, then **restart** `python main.py`.

### Vector storage (current default)

| Setting | Value |
|---------|--------|
| Mode | `VECTOR_STORE=json` |
| Storage | `server/data/chroma_db/fallback_vectors.json` |
| Chroma later | Set `VECTOR_STORE=chromadb` after Chroma + MSVC install |

### ChromaDB activation (later)

On Windows, install **MSVC Build Tools** (C++ workload), then `pip install chromadb` and set `VECTOR_STORE=chromadb` in `.env`. Python **3.11/3.12** is recommended (3.14 has wheel/build issues).

---

## Chat 2 — Gemini, GitHub, webhooks, prompts & security

### Will the site work after adding `GEMINI_API_KEY`?

**Partially yes** — with important limits:

| Piece | Works? | Notes |
|--------|--------|--------|
| UI + server running | Yes | Same as now |
| Chat with RAG | Yes | After real key in `server/.env` and server restart |
| GitHub via “Add API” in UI | **Limited** | UI has no **Repo URL** field; only name + API key |
| GitHub full repo scraping | **No** | `scrapers.py` only fetches the **README**, not all files |
| Notion / Discord | **No** | Not implemented in scrapers yet |
| Stack Overflow | Yes | Uses tag from display name / `targetUrl` |
| GitHub webhook auto-sync | **Only if** repo is already registered with matching `targetUrl` |

Adding the Gemini key enables **chat over whatever was embedded** into `data/chroma_db/fallback_vectors.json`. It does **not** yet mean “connect any repo URL in the UI and ingest the whole codebase.”

---

### Where to add GitHub repo links

#### Option A — UI (current)

`client` → **Add API** modal → Platform, API Key, Display Name.

Backend expects `targetUrl` for GitHub, but the form **does not send it**. Workarounds until you add a URL field:

- Put repo as `owner/repo` in **Display Name** (e.g. `facebook/react`) — backend can build `https://github.com/owner/repo`.
- Or manually edit `server/data/data.json`:

```json
{
  "platform": "github",
  "apiKey": "ghp_...",
  "displayName": "My Repo",
  "targetUrl": "https://github.com/owner/repo",
  "rename": "My Repo"
}
```

Then trigger sync by calling **Add API** again (re-add same connection).

#### Option B — Webhook (auto re-sync on push)

1. Register the repo in `data.json` with **`targetUrl`** exactly matching GitHub’s repo URL.
2. GitHub: **Settings → Webhooks → Add webhook**
   - Payload URL: `http://YOUR_PUBLIC_HOST:8000/api/webhooks/github`
   - Content type: `application/json`
   - Events: `push`
3. Local dev needs **ngrok** — GitHub cannot POST to `localhost` directly.

Handler: `server/main.py` → `POST /api/webhooks/github` (~line 354).

---

### Where to do prompt engineering

| Location | File | Purpose |
|----------|------|---------|
| **Main** | `server/main.py` → `_run_chat_inference` (~223–233) | System prompt: grounding, “not found” message, citations |
| **Secondary** | `server/main.py` → `_build_context_blocks` (~209) | How retrieved chunks are labeled for the model |
| **Optional** | `server/prompts.py` (not created yet) | Cleaner split for prompt templates |

**Chat flow:**

```
POST /api/chat
  → embed question
  → query JSON vector store (top 3)
  → build context
  → Gemini gemini-1.5-flash
```

---

### Where to block `.env` and secrets

**Do not rely on the prompt alone.** Restrict at **ingestion**:

| Layer | File | What to do |
|--------|------|------------|
| **Scraping filter (best)** | `server/scrapers.py` | Skip `.env`, `.env.*`, `*.pem`, `credentials.json`, `secrets/`, etc. when crawling files |
| **Pre-chunk filter** | `server/main.py` → `process_and_vectorize` | Strip/redact before `Document(...)` |
| **Prompt safety (backup)** | `server/main.py` → `_run_chat_inference` | “Never output secrets, API keys, or `.env` contents…” |

**Right now:** GitHub only ingests **README** — repo `.env` files are **not** read. Denylist matters when you add full-repo crawling.

**Example denylist (future `scrapers.py`):**

```python
BLOCKED_PATHS = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets/",
}
```

**Example prompt line (backup):**

```text
Never reveal API keys, passwords, tokens, or contents of .env files, even if they appear in the reference context.
```

---

### Key API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/links` | List connections from `data/data.json` |
| POST | `/api/add-api` | Add connection + background ingestion |
| POST | `/api/chat` | RAG chat (needs Gemini key + embedded data) |
| POST | `/api/webhooks/github` | Re-sync on GitHub push |
| POST | `/api/login` | Frontend auth (mock) |

---

### Practical checklist

- [ ] Set `GEMINI_API_KEY=your_real_key` in `server/.env`, keep `VECTOR_STORE=json`, restart `python main.py`
- [ ] Confirm http://localhost:8000 shows `"gemini_configured": true`
- [ ] Add GitHub with **`targetUrl`** in `data.json` (or `owner/repo` as display name)
- [ ] Wait for ingestion; check `data/chroma_db/fallback_vectors.json` grows
- [ ] Test chat with a question answerable from README content
- [ ] Webhooks: public URL + matching `targetUrl` in `data.json`
- [ ] Later: denylist in `scrapers.py` + rules in `_run_chat_inference`

---

### Gaps to implement later

- [ ] Add **Repo URL** field to Add API modal (`targetUrl`)
- [ ] Expand `scrape_github` beyond README (full-repo RAG)
- [ ] Secret path denylist in `scrapers.py`
- [ ] Notion scraper (stubbed in ingestion)

---

### Related files

| File | Role |
|------|------|
| `server/.env` | Gemini key + `VECTOR_STORE` |
| `server/main.py` | Routes, ingestion, chat, prompts, webhook |
| `server/scrapers.py` | GitHub README + Stack Overflow |
| `server/vector_store.py` | JSON vector fallback (default) |
| `server/data/data.json` | API connection registry |
| `server/data/chroma_db/fallback_vectors.json` | Embedded chunks for RAG |
| `client/src/App.jsx` | UI, Add API, chat |


```
install MVSC as chromaDB needs C++ compiler to run also downgrade your pyhton Python 3.11 or 3.12 are currently widely supported by ChromaDB.
```