"""Evidence filtering and source deduplication module."""

import logging
import re
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

from src.models import FilteredEvidence, RawToolOutput, SourceItem

logger = logging.getLogger("research_agent.filter")

# Heuristics for filtering low-quality or junk text
JUNK_PHRASES = [
    "access denied", "robot or human", "cloudflare", "enable javascript",
    "404 not found", "403 forbidden", "page not found", "captcha verification",
    "all rights reserved", "terms of use", "privacy policy"
]


class EvidenceFilter:
    """Filters noisy, redundant, or low-quality raw tool results into verified evidence sources."""

    def filter_and_index_sources(
        self,
        raw_outputs: List[RawToolOutput],
        original_query: str
    ) -> Tuple[List[SourceItem], str]:
        """
        Processes raw tool outputs into:
        1. Clean, deduplicated, ranked List[SourceItem] with 1-based source_ids
        2. A consolidated evidence context string for synthesis
        """
        seen_urls: Set[str] = set()
        seen_snippets: Set[str] = set()
        sources: List[SourceItem] = []
        evidence_blocks: List[str] = []

        query_terms = set(re.findall(r"\w+", original_query.lower()))

        for output in raw_outputs:
            if not output.success or not output.data:
                continue

            items_to_process = []
            if isinstance(output.data, list):
                items_to_process.extend(output.data)
            elif isinstance(output.data, dict):
                items_to_process.append(output.data)

            for item in items_to_process:
                title = item.get("title", "").strip() or "Web Source"
                url = item.get("url", "").strip()
                raw_snippet = item.get("snippet", "") or item.get("content", "")
                snippet = raw_snippet.strip()

                # Rule 1: Skip if snippet is too short or empty
                if len(snippet) < 35:
                    continue

                # Rule 2: Skip junk or error phrases
                lower_snippet = snippet.lower()
                if any(junk in lower_snippet for junk in JUNK_PHRASES):
                    continue

                # Rule 3: Deduplicate by URL (or title if URL missing)
                norm_url = url.rstrip("/").lower()
                if norm_url and norm_url in seen_urls:
                    continue
                if norm_url:
                    seen_urls.add(norm_url)

                # Rule 4: Deduplicate redundant snippets
                snippet_key = snippet[:80].lower()
                if snippet_key in seen_snippets:
                    continue
                seen_snippets.add(snippet_key)

                # Rule 5: Calculate relevance score based on query term overlap
                snippet_words = set(re.findall(r"\w+", lower_snippet))
                overlap = len(query_terms.intersection(snippet_words))
                relevance = min(1.0, 0.5 + (overlap * 0.1))

                # Extract domain name
                domain = urlparse(url).netloc if url else "web"

                # Assign sequential source ID
                source_id = len(sources) + 1
                source_item = SourceItem(
                    source_id=source_id,
                    title=title,
                    url=url,
                    snippet=snippet[:350],
                    domain=domain,
                    relevance_score=round(relevance, 2)
                )
                sources.append(source_item)

                # Build concise evidence block for LLM synthesis
                evidence_blocks.append(
                    f"Source [{source_id}]: {title} ({domain})\n"
                    f"URL: {url}\n"
                    f"Evidence: {snippet[:450]}\n"
                )

        # If all sources filtered out or no external data, return fallback notice
        if not sources:
            logger.warning("No high-quality sources passed the filter.")
            context = "No verified external sources were successfully retrieved for this inquiry."
        else:
            context = "\n---\n".join(evidence_blocks)

        logger.info(f"Filtering complete. {len(sources)} high-signal sources indexed.")
        return sources, context
