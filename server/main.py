import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from scrapers import DataScrapers
from vector_store import get_knowledge_collection

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Add it to server/.env before starting.")

PLACEHOLDER_KEYS = {"", "YOUR_API_KEY", "your_actual_google_gemini_api_key_here", "your_gemini_key_here"}
GEMINI_READY = GEMINI_API_KEY not in PLACEHOLDER_KEYS

DATA_DIR = "data"
DATA_PATH = os.path.join(DATA_DIR, "data.json")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")
COLLECTION_NAME = "tenant_knowledge"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)

knowledge_collection, vector_backend = get_knowledge_collection(CHROMA_PATH, COLLECTION_NAME)

embeddings_client = None


def _get_embeddings_client():
    global embeddings_client  # noqa: PLW0603
    if not GEMINI_READY:
        return None
    if embeddings_client is None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        embeddings_client = GoogleGenerativeAIEmbeddings(  # type: ignore[misc]
            model="models/text-embedding-004",
            google_api_key=GEMINI_API_KEY,
        )
    return embeddings_client

scrapers = DataScrapers()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=60)

app = FastAPI(title="Multi-Tenant API Connector")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ApiEntry(BaseModel):
    platform: str
    apiKey: str = ""
    displayName: str = ""
    targetUrl: str = ""
    # Legacy frontend field support
    rename: str = ""

    def normalized(self) -> Dict[str, str]:
        display = (self.displayName or self.rename or "").strip()
        return {
            "platform": self.platform.strip().lower(),
            "apiKey": self.apiKey.strip(),
            "displayName": display,
            "targetUrl": self.targetUrl.strip(),
        }


class ChatMessage(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: str
    password: str = ""


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_links() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_links(links: List[Dict[str, Any]]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=4)


def _find_link_index(links: List[Dict[str, Any]], entry: Dict[str, str]) -> int:
    for idx, item in enumerate(links):
        same_platform = item.get("platform", "").lower() == entry["platform"]
        same_name = item.get("displayName", item.get("rename", "")) == entry["displayName"]
        same_url = item.get("targetUrl", "") == entry["targetUrl"]
        if same_platform and same_name and (not entry["targetUrl"] or same_url):
            return idx
    return -1


def _resolve_target_url(entry: Dict[str, str]) -> str:
    if entry.get("targetUrl"):
        return entry["targetUrl"]
    if entry["platform"] == "github" and "/" in entry["displayName"]:
        return f"https://github.com/{entry['displayName']}"
    if entry["platform"] == "stackoverflow":
        return entry["displayName"]
    return ""


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------
async def process_and_vectorize(entry: Dict[str, str]) -> None:
    """
    Scrape source data, chunk it, embed with Gemini, and persist in ChromaDB.
    """
    platform = entry["platform"]
    display_name = entry["displayName"]
    target_url = _resolve_target_url(entry)
    token = entry.get("apiKey", "")

    scraped_text = ""
    if platform == "github":
        if not target_url:
            scraped_text = f"No targetUrl provided for GitHub workspace: {display_name}"
        else:
            scraped_text = await scrapers.scrape_github(target_url, token or None)
    elif platform == "stackoverflow":
        tagged_topic = target_url or display_name
        scraped_text = await scrapers.scrape_stackoverflow(tagged_topic)
    else:
        scraped_text = (
            f"Platform '{platform}' is registered but scraping is not implemented yet "
            f"for workspace '{display_name}'."
        )

    document = Document(
        page_content=scraped_text,
        metadata={
            "source_platform": platform,
            "display_name": display_name,
            "target_url": target_url,
            "harvested_at": _utc_now(),
        },
    )
    chunks = text_splitter.split_documents([document])
    if not chunks:
        return

    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    ids = [f"{platform}:{display_name}:{uuid.uuid4().hex}" for _ in chunks]

    embedder = _get_embeddings_client()
    if embedder is None:
        print(
            "[ingestion] GEMINI_API_KEY is placeholder. Skipping vectorization until a real key is set."
        )
    else:
        vectors = embedder.embed_documents(texts)
        knowledge_collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=vectors,
        )

    links = _read_links()
    for item in links:
        item_platform = item.get("platform", "").lower()
        item_name = item.get("displayName", item.get("rename", ""))
        if item_platform == platform and item_name == display_name:
            item["last_synced"] = _utc_now()
            if target_url:
                item["targetUrl"] = target_url
            break
    _write_links(links)


def _build_context_blocks(results: Dict[str, Any]) -> str:
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    blocks: List[str] = []

    for doc_text, meta in zip(documents, metadatas):
        platform = (meta or {}).get("source_platform", "unknown").upper()
        display_name = (meta or {}).get("display_name", "workspace")
        blocks.append(f"[{platform} Workspace Layer ({display_name})]\n{doc_text}")

    return "\n\n".join(blocks)


def _run_chat_inference(user_message: str, context: str) -> str:
    system_prompt = f"""Role: Act as an elite, direct, developer-friendly internal data RAG assistant.

Grounding Rule: Base answers strictly and exclusively on the text provided inside the reference context window.

Absence Rule: If the provided context block does not contain the answer, do not guess or use outside training data. Reply exactly with: "Information not found in your connected application workspaces."

Inline Citations: Format answer claims using bold markdown source tag citations matching the current source data. For example: "According to your **GitHub (My-Repo)** data, ..."

REFERENCE CONTEXT:
{context if context else "No context available."}
"""

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=GEMINI_API_KEY,
    )
    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", user_message),
        ]
    )
    return getattr(response, "content", str(response))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Multi-Tenant API Connector Server",
        "status": "running",
        "gemini_configured": GEMINI_READY,
        "collection": COLLECTION_NAME,
        "vector_backend": vector_backend,
    }


@app.get("/api/links")
async def get_links():
    try:
        return _read_links()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/add-api")
async def add_api(entry: ApiEntry, background_tasks: BackgroundTasks):
    try:
        normalized = entry.normalized()
        if not normalized["displayName"]:
            raise HTTPException(status_code=400, detail="displayName (or rename) is required")

        links = _read_links()
        existing_idx = _find_link_index(links, normalized)

        record = {
            "platform": normalized["platform"],
            "apiKey": normalized["apiKey"],
            "displayName": normalized["displayName"],
            "targetUrl": normalized["targetUrl"],
            "last_synced": None,
            # Keep legacy key for current frontend compatibility
            "rename": normalized["displayName"],
        }

        if existing_idx >= 0:
            links[existing_idx].update(record)
        else:
            links.append(record)

        _write_links(links)
        background_tasks.add_task(process_and_vectorize, normalized)

        return {
            "status": "success",
            "message": f"Queued ingestion for {normalized['platform']}: {normalized['displayName']}",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat")
async def chat(request: ChatMessage):
    try:
        if not GEMINI_READY:
            return {
                "answer": (
                    "Gemini API key is not configured yet. Set GEMINI_API_KEY in server/.env "
                    "to enable RAG chat responses."
                ),
                "source_used": "system",
                "confidence_score": 0.0,
            }

        embedder = _get_embeddings_client()
        if embedder is None:
            raise HTTPException(status_code=500, detail="Embedding client is not initialized")

        query_embedding = embedder.embed_query(request.message)
        results = knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
        )

        context = _build_context_blocks(results)
        answer = _run_chat_inference(request.message, context)

        metadatas = results.get("metadatas", [[]])[0]
        source_used = "tenant_knowledge"
        if metadatas:
            first = metadatas[0] or {}
            source_used = f"{first.get('source_platform', 'unknown')} ({first.get('display_name', 'workspace')})"

        return {
            "answer": answer,
            "source_used": source_used,
            "confidence_score": 0.85 if context else 0.2,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/webhooks/github")
async def github_webhook(background_tasks: BackgroundTasks, payload: Dict[str, Any] = Body(...)):
    try:
        repository = payload.get("repository", {})
        html_url = repository.get("html_url", "")
        if not html_url:
            raise HTTPException(status_code=400, detail="repository.html_url missing in webhook payload")

        links = _read_links()
        matched = None
        for item in links:
            if item.get("platform", "").lower() != "github":
                continue
            target = item.get("targetUrl", "")
            display = item.get("displayName", item.get("rename", ""))
            if target and target.rstrip("/") == html_url.rstrip("/"):
                matched = item
                break
            if display and display in html_url:
                matched = item
                break

        if not matched:
            return {"status": "ignored", "message": "No matching GitHub workspace found"}

        normalized = {
            "platform": "github",
            "apiKey": matched.get("apiKey", ""),
            "displayName": matched.get("displayName", matched.get("rename", "")),
            "targetUrl": matched.get("targetUrl", html_url),
        }
        background_tasks.add_task(process_and_vectorize, normalized)
        return {"status": "queued", "message": f"Re-sync queued for {normalized['displayName']}"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Legacy endpoints kept for current frontend compatibility
@app.post("/api/login")
async def login(request: LoginRequest):
    user_name = request.email.split("@")[0] if request.email else "user"
    return {"status": "success", "name": user_name, "email": request.email}


@app.delete("/api/link/{index}")
async def delete_link(index: int):
    try:
        links = _read_links()
        if 0 <= index < len(links):
            removed = links.pop(index)
            _write_links(links)
            return {"status": "success", "removed": removed}
        raise HTTPException(status_code=404, detail="Connection not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
