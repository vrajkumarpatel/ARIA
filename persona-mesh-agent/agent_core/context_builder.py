import re
from typing import List, Dict

from .config import config

try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    def _token_count(text: str) -> int:
        return len(_enc.encode(text, disallowed_special=()))
except ImportError:
    def _token_count(text: str) -> int:
        return len(text) // 4


class ContextBuilder:
    """
    THE BRAIN — combines, deduplicates, ranks, and compresses memory.
    ─────────────────────────────────────────────────────────────────
    Pipeline:
        vector results + graph results
            → _process_*()        (format each source)
            → _deduplicate()      (remove near-identical chunks)
            → _rank_by_relevance() (score by keyword overlap)
            → _compress()         (enforce token budget)
            → structured Dict     (ready for persona injection)
    ─────────────────────────────────────────────────────────────────
    Output schema:
    {
        "semantic_memory":   str,   # raw vector hits
        "graph_memory":      str,   # raw graph hits
        "combined_context":  str,   # filtered + compressed
        "summary":           str,   # one-line overview
        "sources":           list,  # ["LlamaIndex", "Neo4j"]
    }
    """

    CHUNK_LIMIT = 500   # max chars per memory chunk before truncation

    # ── Public API ────────────────────────────────────────────

    def build(
        self,
        user_input: str,
        vector_results: List[Dict],
        graph_results: List[Dict],
        conversation_history: List[Dict] = None,
    ) -> Dict:
        semantic = self._process_vectors(vector_results)
        graph    = self._process_graph(graph_results)

        chunks  = self._deduplicate(semantic, graph)
        ranked  = self._rank_by_relevance(chunks, user_input)
        compressed = self._compress(ranked)

        if _token_count(compressed) > config.MAX_CONTEXT_TOKENS:
            # Trim to budget by character approximation then exact check
            compressed = compressed[:config.MAX_CONTEXT_TOKENS * 4]
            compressed += "\n[truncated — token budget reached]"

        sources = []
        if vector_results:
            sources.append("LlamaIndex")
        if graph_results:
            sources.append("Neo4j")

        return {
            "semantic_memory":  semantic,
            "graph_memory":     graph,
            "combined_context": compressed,
            "summary":          self._one_line_summary(ranked, user_input),
            "sources":          sources,
        }

    # ── Sub-processors ────────────────────────────────────────

    def _process_vectors(self, results: List[Dict]) -> str:
        if not results:
            return ""
        lines = []
        for r in results:
            text  = r.get("text", "").strip()[: self.CHUNK_LIMIT]
            score = r.get("score", 0.0)
            if text and score > 0.05:
                lines.append(text)
        return "\n".join(lines)

    def _process_graph(self, results: List[Dict]) -> str:
        if not results:
            return ""
        blocks = []
        for r in results:
            if r.get("reference"):
                body = r.get("response", "")[:300]
                if body:
                    blocks.append(body)
            else:
                q = r.get("user_input", "")[:150]
                a = r.get("response",   "")[:350]
                if q and a:
                    blocks.append(f"{q} — {a}")
                elif q:
                    blocks.append(q)
        return "\n\n".join(blocks)

    def _deduplicate(self, semantic: str, graph: str) -> List[str]:
        """Merge sources and remove near-duplicate chunks (Jaccard ≥ 0.7)."""
        raw = []
        if semantic:
            raw += [c.strip() for c in semantic.split("\n")   if c.strip()]
        if graph:
            raw += [c.strip() for c in graph.split("\n\n")    if c.strip()]

        seen: List[str] = []
        unique: List[str] = []
        for chunk in raw:
            norm = re.sub(r"\s+", " ", chunk.lower())[:120]
            if not any(self._jaccard(norm, s) >= 0.70 for s in seen):
                seen.append(norm)
                unique.append(chunk)
        return unique

    def _rank_by_relevance(self, chunks: List[str], user_input: str) -> List[str]:
        """Score each chunk by keyword overlap with the user's query."""
        keywords = set(re.findall(r"\b\w{3,}\b", user_input.lower()))
        if not keywords:
            return chunks

        scored = []
        for chunk in chunks:
            chunk_words = set(re.findall(r"\b\w{3,}\b", chunk.lower()))
            score = len(keywords & chunk_words)
            scored.append((score, chunk))

        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored]

    def _compress(self, chunks: List[str]) -> str:
        """Build final context string, stopping at the token budget."""
        if not chunks:
            return "No relevant memory found."

        lines, used_tokens = [], 0
        for chunk in chunks:
            excerpt = chunk[: self.CHUNK_LIMIT]
            chunk_tokens = _token_count(excerpt)
            if used_tokens + chunk_tokens > config.MAX_CONTEXT_TOKENS:
                break
            lines.append(excerpt)
            used_tokens += chunk_tokens

        return "\n\n".join(lines) if lines else ""

    def _one_line_summary(self, chunks: List[str], user_input: str) -> str:
        if not chunks:
            return f"No prior memory for: {user_input[:80]}"
        return f"{len(chunks)} chunk(s) retrieved — query: {user_input[:60]}"

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        sa, sb = set(a.split()), set(b.split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)
