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
    """System prompt for Gemini: grounding, tone, format, and safety."""
    scope_line = ""
    if selected_sources:
        names = ", ".join(selected_sources)
        scope_line = (
            f"\nScope: Answer using only knowledge from these connected workspaces: {names}."
        )

    context_body = context if context.strip() else "No context available."

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
