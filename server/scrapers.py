import re
from typing import Optional, Tuple

import httpx


class DataScrapers:
    """Async HTTP scrapers for GitHub and Stack Overflow data extraction."""

    async def scrape_github(self, repo_url: str, token: Optional[str] = None) -> str:
        """
        Parse repo URL into owner/repo and fetch README content from GitHub API.
        """
        owner, repo = self._parse_github_url(repo_url)
        if not owner or not repo:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

        headers = {
            "Accept": "application/vnd.github.raw",
            "User-Agent": "multi-tenant-rag-connector",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()
            return response.text

    async def scrape_stackoverflow(self, tagged_topic: str) -> str:
        """
        Fetch top Stack Overflow questions for a tag via Stack Exchange API.
        """
        api_url = "https://api.stackexchange.com/2.3/questions"
        params = {
            "order": "desc",
            "sort": "votes",
            "tagged": tagged_topic,
            "site": "stackoverflow",
            "pagesize": "5",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, params=params)
            response.raise_for_status()
            payload = response.json()

        items = payload.get("items", [])
        if not items:
            return f"No Stack Overflow questions found for tag: {tagged_topic}"

        lines = [f"Stack Overflow tag: {tagged_topic}", ""]
        for idx, item in enumerate(items, start=1):
            title = item.get("title", "Untitled")
            link = item.get("link", "")
            lines.append(f"{idx}. {title}")
            if link:
                lines.append(f"   Source: {link}")
            lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def _parse_github_url(repo_url: str) -> Tuple[str, str]:
        """
        Supports:
        - https://github.com/owner/repo
        - github.com/owner/repo
        - owner/repo
        """
        cleaned = (repo_url or "").strip().rstrip("/")
        if not cleaned:
            return "", ""

        if "github.com" in cleaned:
            match = re.search(r"github\.com/([^/]+)/([^/]+)", cleaned)
            if match:
                return match.group(1), match.group(2).replace(".git", "")
            return "", ""

        if "/" in cleaned:
            parts = cleaned.split("/")
            if len(parts) >= 2:
                return parts[-2], parts[-1].replace(".git", "")

        return "", ""
