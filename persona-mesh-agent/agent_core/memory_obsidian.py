import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from .entity_extractor import extract_entities, entities_to_line, SPACY_AVAILABLE

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from .config import config


class ObsidianMemory:
    """
    Stores every ARIA conversation turn as a markdown note in an Obsidian vault.
    ─────────────────────────────────────────────────────────────────────────────
    Vault layout:
        ARIA-Memory-Vault/
        ├── Conversations/     ← one note per turn
        ├── Topics/            ← auto-created topic nodes with back-links
        └── _Index.md          ← running index of all turns

    Obsidian's built-in Graph View shows the memory network automatically.
    ─────────────────────────────────────────────────────────────────────────────
    """

    def __init__(self, vault_path: str = None):
        self.vault = Path(vault_path or config.OBSIDIAN_VAULT_PATH)
        self._conv_dir  = self.vault / "Conversations"
        self._topic_dir = self.vault / "Topics"
        self._index     = self.vault / "_Index.md"

        self._conv_dir.mkdir(parents=True, exist_ok=True)
        self._topic_dir.mkdir(parents=True, exist_ok=True)

        if not self._index.exists():
            self._index.write_text("# ARIA Memory Index\n\n", encoding="utf-8")

        print(f"  [Obsidian] Vault: {self.vault}")

    # ── Public API ────────────────────────────────────────────────────────────

    def store_interaction(self, user_input: str, response: str,
                          metadata: Dict = None) -> bool:
        """Write a conversation note and update topic nodes."""
        ts       = datetime.now()
        note_id  = ts.strftime("%Y-%m-%d_%H-%M-%S")
        topics   = self._extract_topics(user_input + " " + response)
        entities = extract_entities(user_input + " " + response)

        # ── Conversation note ─────────────────────────────────────────────────
        topic_links  = "  ".join(f"[[Topics/{t}]]" for t in topics)
        entity_line  = entities_to_line(entities)
        note = (
            f"---\n"
            f"timestamp: {ts.isoformat()}\n"
            f"type: conversation\n"
            f"---\n\n"
            f"**User:** {user_input}\n\n"
            f"**ARIA:** {response}\n\n"
            + (f"{entity_line}\n\n" if entity_line else "")
            + f"## Topics\n{topic_links}\n"
        )
        note_path = self._conv_dir / f"{note_id}.md"
        note_path.write_text(note, encoding="utf-8")

        # ── Topic nodes (upsert) ──────────────────────────────────────────────
        for topic in topics:
            self._upsert_topic(topic, note_id)

        # ── Index append ──────────────────────────────────────────────────────
        with self._index.open("a", encoding="utf-8") as f:
            f.write(f"- {ts.strftime('%H:%M')} [[Conversations/{note_id}]] — "
                    f"{user_input[:60]}\n")

        return True

    # Generic words that appear in every note — useless for ranking
    _SEARCH_STOP = {
        "the","and","for","are","but","not","you","all","can","was","with",
        "this","that","have","from","they","will","been","were","your","just",
        "about","what","how","its","more","also","when","would","could","should",
        "than","then","these","those","their","there","which","while","know",
        "tell","told","said","says","think","want","need","like","okay","yeah",
        "thing","things","some","here","make","does","did","got","get","well",
        "much","very","back","good","great","only","into","over","even","still",
        "right","sure","really","actually","something","anything","everything",
        "using","used","use","lets","let","has","had","him","her","our","out",
        "now","new","see","look","help","sure","give","take","come","going",
        # High-frequency generic words that match too broadly (NOT project/tech terms)
        "done","talk","talking","chat","chatting",
        "nice","meet","meeting","hello",
        "remember","forget","recall","conversation","conversations","discuss",
        "thing","stuff","people","person","someone","anyone","everyone",
    }

    # Patterns that signal the user wants ARIA to recall personal facts
    _IDENTITY_PATTERNS = re.compile(
        r"\b(about me|who am i|what do you know|remember me|know about me"
        r"|tell me about me|my name|what have i told|what did i tell)\b",
        re.IGNORECASE
    )

    def get_related_notes(self, query: str, limit: int = 5) -> List[Dict]:
        """Keyword search across ALL notes — live conversations + imports."""
        raw_kw = set(re.findall(r"\b\w{4,}\b", query.lower()))
        keywords = raw_kw - self._SEARCH_STOP
        if not keywords:
            keywords = raw_kw  # fallback if everything was filtered

        # Identity/profile query — pin ALL reference docs + expand search
        pinned = []
        is_identity = bool(self._IDENTITY_PATTERNS.search(query))
        if is_identity:
            # Pin every top-level reference note (About-*, Showcase-*, etc.)
            for ref_path in sorted(self.vault.glob("*.md")):
                if ref_path.name.startswith("_"):
                    continue
                try:
                    text = ref_path.read_text(encoding="utf-8", errors="ignore")
                    content = "\n".join(
                        l for l in text.splitlines()
                        if l.strip() and not l.startswith("---")
                        and not l.startswith("#") and "[[" not in l
                    )[:400]
                    if content.strip():
                        pinned.append({
                            "user_input": ref_path.stem.replace("-", " "),
                            "response":   content,
                            "note":       ref_path.stem,
                            "source":     "profile",
                            "reference":  True,
                        })
                except Exception:
                    pass
            limit = max(limit, 8)  # Give identity queries more results

        # Collect all searchable .md files (skip topics, index, obsidian config)
        skip_parts = {".obsidian", "Topics", "Imported-Topics"}
        note_files = [
            p for p in self.vault.rglob("*.md")
            if not any(s in p.parts for s in skip_parts)
            and not p.name.startswith("_")
        ]

        # ── Score all notes ───────────────────────────────────────
        note_texts = []
        note_metas = []  # (path, text, lines) per note

        for note_path in note_files:
            try:
                text  = note_path.read_text(encoding="utf-8", errors="ignore")
                lines = text.splitlines()
                is_ref = not any("**User:**" in l or "**You:**" in l
                                  or "**user_input**" in l for l in lines)
                tokens = [w for w in re.findall(r"\b\w{4,}\b", text.lower())
                          if w not in self._SEARCH_STOP]
                note_texts.append(tokens)
                note_metas.append((note_path, text, lines, is_ref))
            except Exception:
                note_texts.append([])
                note_metas.append((note_path, "", [], False))

        if BM25_AVAILABLE and note_texts:
            bm25   = BM25Okapi(note_texts)
            q_tok  = [w for w in re.findall(r"\b\w{4,}\b", " ".join(keywords))
                      if w not in self._SEARCH_STOP] or list(keywords)
            scores = bm25.get_scores(q_tok)
        else:
            # Fallback: keyword count
            scores = [
                sum(1 for kw in keywords if kw in t.lower())
                for _, t, _, _ in note_metas
            ]

        scored = []
        for (note_path, text, lines, is_ref_flag), score in zip(note_metas, scores):
            try:
                # Reference docs surface on any BM25 signal; conversations need more
                min_score = 0.01 if is_ref_flag else (0.5 if BM25_AVAILABLE else 2)
                if score < min_score:
                    continue

                if is_ref_flag:
                    # Reference doc (About-Vraj, Showcase, etc.) — use full content
                    content = "\n".join(
                        l for l in lines
                        if l.strip() and not l.startswith("---")
                        and not l.startswith("#")
                    )[:400]
                    user_input = note_path.stem.replace("-", " ")
                    response   = content
                else:
                    # Conversation note — extract best-matching Q/A window
                    # Strip artifact noise from Claude exports
                    clean_lines = [
                        l for l in lines
                        if "Viewing artifacts created via the Analysis Tool" not in l
                        and l.strip() != "```"
                    ]
                    user_input = next(
                        (l.replace("**You:**","").replace("**User:**","").strip()
                         for l in clean_lines if "**You:**" in l or "**User:**" in l), ""
                    )
                    # Collect ALL assistant turns, join for richer context
                    assistant_turns = [
                        l.split(":**",1)[-1].strip()
                        for l in clean_lines
                        if ":**" in l and "You" not in l and "User" not in l
                        and "**" in l and l.strip()
                    ]
                    response = " … ".join(t for t in assistant_turns if t)[:400]

                source = "obsidian"
                if "Imported" in note_path.parts:
                    idx = note_path.parts.index("Imported")
                    source = note_path.parts[idx + 1] if idx + 1 < len(note_path.parts) else "import"

                scored.append((score, {
                    "user_input": (user_input or note_path.stem)[:200],
                    "response":   response[:200],
                    "note":       note_path.stem,
                    "source":     source,
                    "reference":  is_ref_flag,
                }))
            except Exception:
                pass

        scored.sort(key=lambda x: -x[0])
        results = [item for _, item in scored[:limit]]
        # Prepend pinned profile notes, avoid duplicates
        pinned_notes = {p["note"] for p in pinned}
        results = pinned + [r for r in results if r["note"] not in pinned_notes]
        return results[:limit]

    def get_all_stats(self) -> Dict:
        notes  = list(self._conv_dir.glob("*.md"))
        topics = list(self._topic_dir.glob("*.md"))
        return {
            "vault":            str(self.vault),
            "conversation_notes": len(notes),
            "topic_nodes":      len(topics),
            "latest":           notes[-1].stem if notes else None,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic keywords. Uses spaCy entities when available."""
        STOP = {"the","and","for","are","but","not","you","all","can","was",
                "with","this","that","have","from","they","will","been","were",
                "aria","user","about","just","know","what","your","how","its"}

        topics, seen = [], set()

        if SPACY_AVAILABLE:
            # Prefer named entities as topics — much more meaningful
            for ent in extract_entities(text):
                name = ent["text"].split()[0].capitalize()  # first token of entity
                if name.lower() not in STOP and name not in seen and len(name) >= 3:
                    seen.add(name)
                    topics.append(name)
                if len(topics) >= 6:
                    return topics

        # Fill remaining slots with keyword extraction
        words = re.findall(r"\b[a-zA-Z]{4,20}\b", text)
        for w in words:
            wl = w.lower()
            if wl not in STOP and wl not in seen:
                seen.add(wl)
                topics.append(w.capitalize())
            if len(topics) >= 6:
                break
        return topics

    def _upsert_topic(self, topic: str, note_id: str):
        """Add a back-link to a topic node, creating the file if needed."""
        path = self._topic_dir / f"{topic}.md"
        link = f"- [[Conversations/{note_id}]]\n"
        if path.exists():
            path.open("a", encoding="utf-8").write(link)
        else:
            path.write_text(f"# {topic}\n\n{link}", encoding="utf-8")
