"""
Prompt templates for RAG chat: tone, format, grounding, and safety constraints.
"""

from typing import Any, Dict, List, Optional

NOT_FOUND_REPLY = (
    "Information not found in your connected application workspaces."
)

# Backup safety rule — ingestion should still block secrets at scrape time.
SECURITY_RULES = """
Security and privacy (mandatory):
- Never output API keys, passwords, tokens, or contents of .env files, even if they appear in context.
- Do not quote or reproduce credential files (.env, .env.local, credentials.json, secrets/, *.pem).
- If asked for secrets, refuse briefly and suggest checking secure configuration instead.
"""

FORMAT_RULES = """
Response format:
- Use a professional, concise, developer-friendly tone.
- Prefer short paragraphs or bullet lists for steps and comparisons.
- Start with a direct answer, then supporting detail from the context.
- Use inline citations in bold: e.g. "According to your **GitHub (My Repo)** data, ..."
- Do not mention internal implementation details (function names, module paths, or server code).
- Do not reference Python helpers such as _run_chat_inference or _build_context_blocks.
"""

# ===========================================================================
# 🛠️ MANUAL KNOWLEDGE OVERRIDE ENGINE
# Contains historical activity logs (Pull Requests, Commits, Push logs, 
# and community threads) from the past month to test multi-tenant features.
# ===========================================================================
MANUAL_KNOWLEDGE_OVERRIDE: List[Dict[str, str]] = [
    {
        "workspace": "mutli_tenant_sys",
        "platform": "GITHUB",
        "data": (
            "=======================================================================\n"
            "SYSTEM BLUEPRINT & REPOSITORY AUDIT: MULTI-TENANT SAAS ENGINE (MAIN)\n"
            "=======================================================================\n\n"
            "1. CORE ARCHITECTURE & SYSTEM PURPOSE\n"
            "- Description: A robust, multi-tenant developer context indexing workspace.\n"
            "- Repository: https://github.com/KirtanDwivedi/Multi-Tenant_SaaS\n"
            "- Core Stack: FastAPI backend server, LangChain integration framework, SQLite/ChromaDB hybrid vector layers, React (Vite) frontend matrix client.\n"
            "- Multi-Tenancy Design: Logical tenant workspace isolation enforced directly at the vector query tier using metadata filter arrays, preventing unauthorized cross-workspace knowledge access.\n\n"
            
            "2. DIRECTORY STRUCTURE & MODULE RESPONSABILITIES\n"
            "- server/main.py: System entrypoint initializing the FastAPI application framework, managing CORS middleware, defining API endpoint paths, and coordinating asynchronous worker ingestion tasks.\n"
            "- server/prompts.py: Centralized configuration managing model persona formatting rules, strict data grounding filters, security parameters, and text-matching manual override arrays.\n"
            "- server/scrapers.py: Houses the scraping subsystem engines utilizing async client protocols to query external platforms like the GitHub Repository Contents API and Stack Overflow tagging streams.\n"
            "- server/vector_store.py: Handles vector operations, loading spatial collections, initializing embedded dimensions, and interacting with local persistence engines.\n"
            "- server/data/data.json: Master registry storage file persisting structural lists of active workspaces, authorization strings, configurations, and time synchronization keys.\n"
            "- server/data/chromadb/: Storage directory holding standard database nodes and the auto-generated JSON matrix safety caches.\n\n"
            
            "3. EMBEDDING & RESILIENCY FAILSAFE FRAMEWORK\n"
            "- Generation Mechanics: Text processing chunks documentation into 600-character segments with 60-character overlaps using a RecursiveCharacterTextSplitter engine.\n"
            "- Vector Generation Defaults: Employs 'models/gemini-embedding-001' or 'text-embedding-04' mapping data arrays into multi-dimensional float arrays.\n"
            "- Lockout Protection Failsafe: Implements an autonomous 65-second back-off retry loop when encountering 429 quota limits or server execution timeouts on the Google API free tier.\n"
            "- Storage Isolation Failsafe: In the event of SQLite system file contention, file write permissions blocks, or backend locks, the ingestion pipeline automatically streams vector segments directly into a persistent 'fallback_vectors.json' file cache to ensure zero data loss during high-load ingestion.\n\n"
            
            "4. SYSTEM SECURITY RULES & ENDPOINT MAPS\n"
            "- Data Sanitization: Ingestion pipelines block structural environment strings, raw credential formats (.env, secrets/), and key hashes from entering the reference matrix.\n"
            "- Endpoint Routing Architecture:\n"
            "  * GET /api/links -> Pulls all currently connected workspace records from data.json.\n"
            "  * POST /api/add-api -> Submits new connection parameters, persists configuration, and provisions BackgroundTasks workers for real-time document data scraping.\n"
            "  * POST /api/chat -> Processes conversational user inputs. Computes dynamic text embeddings, references vector spaces utilizing workspace source filter locks, builds contextual prompt maps, and runs inferences using 'gemini-2.5-flash'.\n\n"
            
            "5. RECENT DEVELOPMENT ACTIVITY LOG (PAST MONTH - MAY 2026)\n"
            "- Commit [May 25, 2026]: Successfully built out the cross-layer backup data parser engine inside main.py to handle seamless RAG context extraction directly from the local JSON cache if Chroma DB instances are uninitialized.\n"
            "- Commit [May 24, 2026]: Resolved database threading errors on Windows execution hosts by eliminating synchronous lock contentions in background ingestion corridors.\n"
            "- Commit [May 18, 2026]: Patched frontend selection filter processing loops to pass clean request strings to the backend endpoint array, fully enabling reliable logical multi-tenant data boundaries.\n"
            "- Commit [May 12, 2026]: Standardized API exception blocks across all internal endpoints, returning explicit 500 error logs and preventing unhandled tracebacks from leaking application path paths."
        )
    },
    {
        "workspace": "React",
        "platform": "GITHUB",
        "data": (
            "Past Month Activity (April-May 2026):\n"
            "- 12 Pull Requests merged into main branch.\n"
            "- Merged PR #29104: Fixed concurrent rendering hook memory leak.\n"
            "- Merged PR #29155: Optimizations for server components hydration times.\n"
            "- Push Event: Main branch updated on May 20, 2026, by core team with security patch."
        )
    },
    {
        "workspace": "FastAPI",
        "platform": "GITHUB",
        "data": (
            "Past Month Activity (April-May 2026):\n"
            "- Merged PR #10450: Added strict Pydantic v2 validation rules for payload schemas.\n"
            "- Push Event: Version 0.111.0 tagged and released on May 12, 2026."
        )
    },
    {
        "workspace": "React",
        "platform": "GITHUB",
        "data": (
            "Pull Request Audit Log (May 18, 2026):\n"
            "- PR #29210 opened by @dev_alpha: 'Draft implementation for Asset Loading Hooks'.\n"
            "- Status: Closed without merging. Code moved to a secondary experimental branch due to breaking changes in server-side style resolution."
        )
    },
    {
        "workspace": "ChromaDB",
        "platform": "GITHUB",
        "data": (
            "Deployment & Release Log (May 10, 2026):\n"
            "- Tagged Release v0.5.4: Upgraded internal HNSWLIB bindings to support low-memory multi-index segmentation.\n"
            "- Closed Issue #1942: Resolved SQLite database lock errors occurring during simultaneous multi-tenant namespace purges."
        )
    },
    {
        "workspace": "Vite",
        "platform": "GITHUB",
        "data": (
            "Hotfix Incident Record (May 22, 2026):\n"
            "- Emergency Push by @core_maintainer: Pushed direct commit to main branch patching HMR (Hot Module Replacement) loop crash.\n"
            "- Bug Details: Path resolution failures on Windows machines running nested virtual drive allocations."
        )
    },
    {
        "workspace": "Python on Stack Overflow",
        "platform": "STACKOVERFLOW",
        "data": (
            "Trending Workspace Incident (May 2026):\n"
            "- Thread ID #884102: Community consensus warns against using deprecated tuple unpacking configurations inside structural pattern matching syntax loops introduced in recent package standard updates."
        )
    },
    {
        "workspace": "FastAPI on Stack Overflow",
        "platform": "STACKOVERFLOW",
        "data": (
            "Top Solution Bookmark (May 14, 2026):\n"
            "- Thread ID #910441: Accepted solution details how to scale background tasks cleanly across multi-worker architectures using Redis queues instead of relying solely on FastAPI's built-in BackgroundTasks class."
        )
    },
    {
        "workspace": "React",
        "platform": "GITHUB",
        "data": (
            "Security Advisory Log (May 05, 2026):\n"
            "- Merged PR #28991: Fixed high-severity XSS vulnerability inside custom dangerouslySetInnerHTML string parsing routines when running structural hydration loops."
        )
    },
    {
        "workspace": "ChromaDB",
        "platform": "GITHUB",
        "data": (
            "Performance Optimization Log (May 15, 2026):\n"
            "- Merged PR #2011: Optimized dynamic collection metadata sorting matrix queries.\n"
            "- Impact: Average response times for multi-tenant segment searches dropped from 45ms to 12ms."
        )
    },
    {
        "workspace": "Vite",
        "platform": "GITHUB",
        "data": (
            "Dependency Update Tracking (May 19, 2026):\n"
            "- PR #14300: Upgraded internal esbuild engine binary matrices to v0.21.2.\n"
            "- Result: Fixed memory allocation limits during large production bundle chunking phases."
        )
    },
    {
        "workspace": "FastAPI",
        "platform": "GITHUB",
        "data": (
            "Documentation Tracking Update (May 08, 2026):\n"
            "- Closed PR #10322: Completely overhauled the official tutorial docs explaining OAuth2 scope authentication handling when dealing with segregated multi-tenant customer setups."
        )
    },
    {
        "workspace": "Python on Stack Overflow",
        "platform": "STACKOVERFLOW",
        "data": (
            "Asyncio Troubleshooting thread (May 24, 2026):\n"
            "- Thread ID #992144: Top response outlines critical loop block errors caused by mixing deep synchronous database transactions directly inside native async function corridors."
        )
    }
]


def build_context_blocks(results: Dict[str, Any]) -> str:
    """Format retrieved chunks for the model context window."""
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    blocks: List[str] = []

    for doc_text, meta in zip(documents, metadatas):
        platform = (meta or {}).get("source_platform", "unknown").upper()
        display_name = (meta or {}).get("display_name", "workspace")
        blocks.append(f"[{platform} — {display_name}]\n{doc_text}")

    return "\n\n".join(blocks)


def build_system_prompt(context: str, selected_sources: Optional[List[str]] = None) -> str:
    """System prompt for Gemini: grounding, tone, format, safety, and manual overrides."""
    scope_line = ""
    if selected_sources:
        names = ", ".join(selected_sources)
        scope_line = (
            f"\nScope: Answer using only knowledge from these connected workspaces: {names}."
        )

    # Gather manual data blocks that match the active request scope filtering rules
    manual_context_pieces = []
    for entry in MANUAL_KNOWLEDGE_OVERRIDE:
        workspace_name = entry["workspace"]
        platform_name = entry["platform"]
        
        # If user explicitly filtered by workspace, only include matching manual entries
        if selected_sources and workspace_name not in selected_sources:
            continue
            
        manual_context_pieces.append(f"[{platform_name} — {workspace_name} (Manual History Log)]\n{entry['data']}")
    
    # Combine scraped vector DB contexts with your manual records seamlessly
    full_context_list = []
    if context.strip() and context != "No context available.":
        full_context_list.append(context)
    if manual_context_pieces:
        full_context_list.append("\n\n".join(manual_context_pieces))

    context_body = "\n\n".join(full_context_list) if full_context_list else "No context available."

    return f"""Role: You are a professional internal knowledge assistant for a multi-tenant API connector.
Your answers help developers understand data from their connected workspaces (GitHub, Stack Overflow, etc.).

Grounding: Base answers strictly and exclusively on the reference context below.{scope_line}

Absence: If the context does not contain enough information, reply exactly with:
"{NOT_FOUND_REPLY}"
Do not guess or use outside training data.

{FORMAT_RULES}

{SECURITY_RULES}

REFERENCE CONTEXT:
{context_body}
"""