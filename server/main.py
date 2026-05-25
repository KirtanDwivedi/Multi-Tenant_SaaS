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

from prompts import NOT_FOUND_REPLY, build_context_blocks, build_system_prompt
from scrapers import DataScrapers
from vector_store import get_knowledge_collection, query_collection

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Add it to server/.env before starting.")

PLACEHOLDER_KEYS = {"", "YOUR_API_KEY", "your_actual_google_gemini_api_key_here", "your_gemini_key_here"}
GEMINI_READY = GEMINI_API_KEY not in PLACEHOLDER_KEYS

# Force absolute pathing relative to the script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATA_PATH = os.path.join(DATA_DIR, "data.json")
CONTENT_PATH = os.path.join(DATA_DIR, "content.json")
FALLBACK_PATH = os.path.join(DATA_DIR, "chromadb", "fallback_vectors.json")

# Match folder layout
CHROMA_PATH = os.path.join(DATA_DIR, "chromadb")
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

        # Default model with text-embedding fallback handling
        embeddings_client = GoogleGenerativeAIEmbeddings(  # type: ignore[misc]
            model="models/gemini-embedding-001",
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
    sources: List[str] = []


class LoginRequest(BaseModel):
    email: str
    password: str = ""


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_links() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


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
# Fallback Vector Parser Engine
# ---------------------------------------------------------------------------
def _query_fallback_json(query_text: str, source_filters: Optional[List[str]] = None) -> Dict[str, List]:
    """
    Simulates ChromaDB outputs by matching documents from the backup fallback JSON cache file.
    """
    results = {"documents": [[]], "metadatas": [[]], "ids": [[]]}
    if not os.path.exists(FALLBACK_PATH):
        return results

    try:
        with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
            cached_data = json.load(f)

        matched_records = []
        for item in cached_data:
            meta = item.get("metadata", {})
            display_name = meta.get("display_name", "")

            # Apply strict scoping query filter maps if supplied by request
            if source_filters and display_name not in source_filters:
                continue
            matched_records.append(item)

        # Basic text matching fallback logic
        query_words = query_text.lower().split()
        scored_records = []
        for item in matched_records:
            doc_content = item.get("document", "").lower()
            score = sum(1 for word in query_words if word in doc_content)
            scored_records.append((score, item))

        scored_records.sort(key=lambda x: x[0], reverse=True)
        top_3 = scored_records[:3]

        for _, item in top_3:
            results["documents"][0].append(item.get("document", ""))
            results["metadatas"][0].append(item.get("metadata", {}))
            results["ids"][0].append(item.get("id", ""))

    except Exception as e:
        print(f"[Fallback Parser Exception] Reading fallback matrix failed: {e}")

    return results


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------
async def process_and_vectorize(entry: Dict[str, str]) -> None:
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
        print("[ingestion] GEMINI_API_KEY is placeholder. Skipping vectorization.")
    else:
        try:
            vectors = embedder.embed_documents(texts)
            knowledge_collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=vectors,
            )
        except Exception as vec_err:
            print(f"[Ingestion Error] Writing directly to Chroma database matrix failed: {vec_err}")
            # Automatically save locally if the direct SQLite injection fails
            fallback_records = []
            if os.path.exists(FALLBACK_PATH):
                try:
                    with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
                        fallback_records = json.load(f)
                except Exception:
                    pass
            for chunk_id, txt, mt in zip(ids, texts, metadatas):
                fallback_records.append({"id": chunk_id, "document": txt, "metadata": mt})
            with open(FALLBACK_PATH, "w", encoding="utf-8") as f:
                json.dump(fallback_records, f, indent=2)

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


def _run_chat_inference(
    user_message: str,
    context: str,
    selected_sources: Optional[List[str]] = None,
) -> str:
    system_prompt = build_system_prompt(context, selected_sources)

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        api_key=GEMINI_API_KEY,
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
        "vector_backend": "chroma_with_fallback" if os.path.exists(FALLBACK_PATH) else vector_backend,
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
                "answer": "Gemini API key is not configured yet. Set GEMINI_API_KEY in server/.env.",
                "source_used": "system",
                "confidence_score": 0.0,
            }

        embedder = _get_embeddings_client()
        if embedder is None:
            raise HTTPException(status_code=500, detail="Embedding client is not initialized")

        source_filters = [s.strip() for s in request.sources if s.strip()]
        
        # Flag to check if standard chroma data returned rows
        has_chroma_records = False
        results = {"documents": [[]], "metadatas": [[]], "ids": [[]]}

        try:
            query_embedding = embedder.embed_query(request.message)
            results = query_collection(
                knowledge_collection,
                query_embeddings=[query_embedding],
                n_results=3,
                source_filters=source_filters or None,
            )
            if results and results.get("documents") and results["documents"][0]:
                has_chroma_records = True
        except Exception as chroma_err:
            print(f"[Runtime Safety Alert] Direct Chroma Query failed: {chroma_err}. Checking fallback index...")

        # Execute fallback query parsing if SQLite collections return empty blocks
        if not has_chroma_records:
            results = _query_fallback_json(request.message, source_filters=source_filters or None)

        context = build_context_blocks(results)
        answer = _run_chat_inference(
            request.message,
            context,
            selected_sources=source_filters or None,
        )

        # Extract safely to avoid IndexError strings
        metadatas = results.get("metadatas", [[]])[0]
        source_used = "tenant_knowledge"
        
        if source_filters:
            source_used = ", ".join(source_filters)
        elif metadatas and len(metadatas) > 0:
            first = metadatas[0] or {}
            source_used = f"{first.get('source_platform', 'fallback')} ({first.get('display_name', 'workspace')})"

        if source_filters and not context.strip():
            answer = NOT_FOUND_REPLY

        return {
            "answer": answer,
            "source_used": source_used,
            "confidence_score": 0.85 if context.strip() else 0.2,
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