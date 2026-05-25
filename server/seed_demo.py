"""
Fetch real GitHub README and Stack Overflow API data, then seed data.json,
content.json, and the vector store.

Usage (from server/ with venv active):
    python seed_demo.py

Set GEMINI_API_KEY in .env for Gemini embeddings (recommended).
Without a real key, vectors are skipped — JSON files are still written.
"""

import asyncio
import html
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import time

import httpx
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from scrapers import DataScrapers
from vector_store import get_knowledge_collection

# --- BULLETPROOF ERROR CATCHING IMPORTS ---
try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = Exception

try:
    from langchain_google_genai._common import GoogleGenerativeAIError
except ImportError:
    GoogleGenerativeAIError = Exception
# ------------------------------------------

load_dotenv()


# Force absolute pathing relative to the script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATA_PATH = os.path.join(DATA_DIR, "data.json")
CONTENT_PATH = os.path.join(DATA_DIR, "content.json")

# Match your exact folder layout (chromadb instead of chroma_db)
CHROMA_PATH = os.path.join(DATA_DIR, "chromadb")
COLLECTION_NAME = "tenant_knowledge"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PLACEHOLDER_KEYS = {"", "YOUR_API_KEY", "your_actual_google_gemini_api_key_here", "your_gemini_key_here"}

# Six live sources — same shapes the production scrapers use (GitHub README + SO questions).
CONNECTIONS: List[Dict[str, Any]] = [
    {
        "platform": "github",
        "apiKey": "",
        "displayName": "React",
        "targetUrl": "https://github.com/facebook/react",
        "rename": "React",
    },
    {
        "platform": "github",
        "apiKey": "",
        "displayName": "FastAPI",
        "targetUrl": "https://github.com/fastapi/fastapi",
        "rename": "FastAPI",
    },
    {
        "platform": "github",
        "apiKey": "",
        "displayName": "ChromaDB",
        "targetUrl": "https://github.com/chroma-core/chroma",
        "rename": "ChromaDB",
    },
    {
        "platform": "github",
        "apiKey": "",
        "displayName": "Vite",
        "targetUrl": "https://github.com/vitejs/vite",
        "rename": "Vite",
    },
    {
        "platform": "stackoverflow",
        "apiKey": "",
        "displayName": "Python on Stack Overflow",
        "targetUrl": "python",
        "rename": "Python on Stack Overflow",
    },
    {
        "platform": "stackoverflow",
        "apiKey": "",
        "displayName": "FastAPI on Stack Overflow",
        "targetUrl": "fastapi",
        "rename": "FastAPI on Stack Overflow",
    },
]

# Cap README size so seed stays fast; 12k chars is plenty for RAG chunks.
README_CHAR_LIMIT = 12000
SO_PAGESIZE = 12
SO_BODY_LIMIT = 3000


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n[... truncated for storage ...]"


async def fetch_github_readme(repo_url: str) -> str:
    """GitHub REST: GET /repos/{owner}/{repo}/readme (raw markdown)."""
    scrapers = DataScrapers()
    readme = await scrapers.scrape_github(repo_url, token=None)
    owner, repo = scrapers._parse_github_url(repo_url)
    header = (
        f"GitHub README harvest\n"
        f"Repository: https://github.com/{owner}/{repo}\n"
        f"API endpoint: GET /repos/{owner}/{repo}/readme (Accept: application/vnd.github.raw)\n\n"
    )
    return header + _truncate(readme.strip(), README_CHAR_LIMIT)


async def fetch_stackoverflow_tag(tag: str) -> str:
    """
    Stack Exchange API 2.3: top voted questions for a tag with full question bodies.
    https://api.stackexchange.com/docs/questions
    """
    params = {
        "order": "desc",
        "sort": "votes",
        "tagged": tag,
        "site": "stackoverflow",
        "pagesize": SO_PAGESIZE,
        "filter": "withbody",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get("https://api.stackexchange.com/2.3/questions", params=params)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", [])

        if not items:
            return f"No Stack Overflow questions returned for tag: {tag}"

        lines = [
            "Stack Overflow harvest",
            f"Tag: {tag}",
            "API: Stack Exchange 2.3 GET /questions (sort=votes, filter=withbody)",
            f"Questions returned: {len(items)}",
            "",
        ]

        for idx, item in enumerate(items, start=1):
            title = item.get("title", "Untitled")
            link = item.get("link", "")
            score = item.get("score", 0)
            views = item.get("view_count", 0)
            answers = item.get("answer_count", 0)
            tags = ", ".join(item.get("tags", []))
            body = _truncate(_strip_html(item.get("body", "")), SO_BODY_LIMIT)

            lines.extend(
                [
                    f"--- Question {idx} ---",
                    f"Title: {title}",
                    f"Score: {score} | Views: {views} | Answers: {answers}",
                    f"Tags: {tags}",
                    f"URL: {link}",
                    "",
                    "Question body:",
                    body,
                    "",
                ]
            )

            qid = item.get("question_id")
            if qid and answers and idx <= 6:
                answer_text = await _fetch_top_answer(client, qid)
                if answer_text:
                    lines.extend(["Top answer excerpt:", _truncate(answer_text, 2000), ""])

    return "\n".join(lines).strip()


async def _fetch_top_answer(client: httpx.AsyncClient, question_id: int) -> str:
    params = {
        "order": "desc",
        "sort": "votes",
        "site": "stackoverflow",
        "pagesize": 1,
        "filter": "withbody",
    }
    url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
    response = await client.get(url, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])

    if not items:
        return ""
    answer = items[0]
    score = answer.get("score", 0)
    body = _strip_html(answer.get("body", ""))
    return f"(score {score}) {body}"


async def fetch_all_content() -> List[Dict[str, str]]:
    harvested: List[Dict[str, str]] = []

    for conn in CONNECTIONS:
        name = conn["displayName"]
        platform = conn["platform"]
        target = conn["targetUrl"]
        print(f"Fetching {platform}: {name} ...")

        if platform == "github":
            text = await fetch_github_readme(target)
        elif platform == "stackoverflow":
            text = await fetch_stackoverflow_tag(target)
        else:
            text = f"Platform '{platform}' is not supported by seed fetch."

        harvested.append({"workspace": name, "platform": platform, "text": text})
        print(f"  -> {len(text):,} characters")

    return harvested


def _get_embedder():
    if GEMINI_API_KEY in PLACEHOLDER_KEYS:
        return None
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY,
    )


def _clear_collection(collection) -> None:
    if hasattr(collection, "records"):
        collection.records = []
        collection._persist()
        return
    try:
        existing = collection.get()
        ids = existing.get("ids") or []
        if ids:
            collection.delete(ids=ids)
    except Exception:
        pass


def _write_json_files(harvested: List[Dict[str, str]], synced: Optional[str] = None) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    links = []
    for conn in CONNECTIONS:
        record = dict(conn)
        record["last_synced"] = synced
        links.append(record)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=4)
    print(f"Wrote {DATA_PATH} ({len(links)} connections)")

    content_records = []
    for item in harvested:
        content_records.append(
            {
                "source": item["workspace"],
                "platform": item["platform"],
                "text": item["text"].strip(),
                "char_count": len(item["text"]),
                "created_at": synced or _utc_now(),
            }
        )

    with open(CONTENT_PATH, "w", encoding="utf-8") as f:
        json.dump(content_records, f, indent=2)

    cache_path = os.path.join(DATA_DIR, "harvested_cache.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(harvested, f, indent=2)
    print(f"Wrote {CONTENT_PATH} ({len(content_records)} entries)")


def _embed_harvest(harvested: List[Dict[str, str]], embedder) -> int:
    collection, backend = get_knowledge_collection(CHROMA_PATH, COLLECTION_NAME)
    _clear_collection(collection)
    print(f"Vector backend: {backend}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    all_ids: List[str] = []
    all_texts: List[str] = []
    all_metas: List[Dict[str, Any]] = []

    for item in harvested:
        target_url = next(
            (c["targetUrl"] for c in CONNECTIONS if c["displayName"] == item["workspace"]),
            "",
        )
        doc = Document(
            page_content=item["text"].strip(),
            metadata={
                "source_platform": item["platform"],
                "display_name": item["workspace"],
                "target_url": target_url,
                "harvested_at": _utc_now(),
            },
        )
        for chunk in splitter.split_documents([doc]):
            all_ids.append(f"{item['platform']}:{item['workspace']}:{uuid.uuid4().hex}")
            all_texts.append(chunk.page_content)
            all_metas.append(chunk.metadata)

    print(f"Embedding {len(all_texts)} chunks in rate-limited batches with auto-retry...")
    
    # --- BULLETPROOF RETRY LOOP IMPLEMENTATION ---
    BATCH_SIZE = 25  # Lower structural density to balance global Token-Per-Minute restrictions
    vectors = []
    
    i = 0
    while i < len(all_texts):
        batch_texts = all_texts[i:i + BATCH_SIZE]
        current_batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(all_texts) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  -> Processing batch {current_batch_num}/{total_batches} ({len(batch_texts)} chunks)...")
        
        try:
            batch_vectors = embedder.embed_documents(batch_texts)
            vectors.extend(batch_vectors)
            i += BATCH_SIZE  # Progress only when the API cleanly responds
            
            # Short proactive rest period between successful processing windows
            if i < len(all_texts):
                time.sleep(4.0)
                
        except (ResourceExhausted, GoogleGenerativeAIError, Exception) as e:
            # Handle the 429 quota exception explicitly, sleep off the lock, then recalculate
            print(f"\n[!] Rate limit reached or backend timeout encountered.")
            print(f"    Details: {e}")
            print("    Pausing execution for 25 seconds to clear Google API Free Tier quota tokens...")
            time.sleep(25.0)
            print("    Resuming and retrying current batch transaction...\n")
    # ---------------------------------------------

    collection.add(ids=all_ids, documents=all_texts, metadatas=all_metas, embeddings=vectors)
    print(f"Stored {len(all_texts)} vectors in {backend}.")
    return len(all_texts)


async def async_main() -> None:
    os.makedirs(CHROMA_PATH, exist_ok=True)
    harvested = await fetch_all_content()
    synced = _utc_now()

    embedder = _get_embedder()
    if embedder is None:
        print("\nGEMINI_API_KEY not set — wrote JSON only. Add your key and re-run to embed.")
        collection, _ = get_knowledge_collection(CHROMA_PATH, COLLECTION_NAME)
        _clear_collection(collection)
        _write_json_files(harvested, synced=synced)
        return

    chunk_count = _embed_harvest(harvested, embedder)
    _write_json_files(harvested, synced=synced)
    print(f"Done. {len(CONNECTIONS)} sources, {chunk_count} vector chunks ready for chat.")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()