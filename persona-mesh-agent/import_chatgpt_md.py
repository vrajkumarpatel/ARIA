#!/usr/bin/env python3
"""
Import C:\CHATGPT markdown files → Obsidian Memory Vault
Handles the # User / # ChatGPT format with HTML-tagged responses.

Usage:
  python import_chatgpt_md.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

CHATGPT_DIR = Path(r"C:\CHATGPT")
VAULT       = Path(r"C:\ARIA\ARIA-Memory-Vault")
OUT_DIR     = VAULT / "Imported" / "ChatGPT"
TOPIC_DIR   = VAULT / "Imported-Topics"

STOP = {
    "the","and","for","are","but","not","you","all","can","was","with",
    "this","that","have","from","they","will","been","were","your","just",
    "about","what","how","its","more","also","when","would","could",
    "should","than","then","these","those","their","there","which","while",
    "user","chatgpt","reply","short","human","words","write","rewrite",
}

SEPARATOR = re.compile(r"-{10,}")
HTML_TAG  = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return HTML_TAG.sub("", text).strip()


def extract_topics(text: str, max_topics: int = 8) -> list[str]:
    words = re.findall(r"\b[a-zA-Z]{4,25}\b", text)
    seen, topics = set(), []
    for w in words:
        wl = w.lower()
        if wl not in STOP and wl not in seen:
            seen.add(wl)
            topics.append(w.capitalize())
        if len(topics) >= max_topics:
            break
    return topics


def parse_md(path: Path) -> list[dict]:
    """Return list of {role, content} dicts from a ChatGPT export .md file."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # Split on the horizontal rule separators
    blocks = SEPARATOR.split(raw)
    turns = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("# User"):
            content = block[len("# User"):].strip()
            if content:
                turns.append({"role": "user", "content": content[:600]})
        elif block.startswith("# ChatGPT"):
            content = strip_html(block[len("# ChatGPT"):].strip())
            if content:
                turns.append({"role": "assistant", "content": content[:600]})
    return turns


def ts_from_filename(path: Path) -> datetime:
    """Parse timestamp from ChatGPT_YYYY-MM-DD-HH-MM-SS.md"""
    try:
        stem = path.stem  # e.g. ChatGPT_2026-05-01-02-18-00
        parts = stem.split("_", 1)
        dt_str = parts[1]  # 2026-05-01-02-18-00
        return datetime.strptime(dt_str, "%Y-%m-%d-%H-%M-%S").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(tz=timezone.utc)


def write_note(note_id: str, title: str, turns: list[dict], ts: datetime):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{note_id}.md"
    if path.exists():
        return False  # skip duplicates

    full_text = " ".join(t["content"] for t in turns)
    topics = extract_topics(full_text)

    lines = [
        "---",
        "source: ChatGPT",
        f"timestamp: {ts.isoformat()}",
        f"title: {title[:80]}",
        "---",
        "",
        f"# {title[:80]}",
        "",
    ]

    for turn in turns:
        label = "**You:**" if turn["role"] == "user" else "**ChatGPT:**"
        lines.append(f"{label} {turn['content']}")
        lines.append("")

    if topics:
        topic_links = "  ".join(f"[[Imported-Topics/{t}]]" for t in topics)
        lines += ["## Topics", topic_links, ""]

    path.write_text("\n".join(lines), encoding="utf-8")

    # Upsert topic nodes
    TOPIC_DIR.mkdir(exist_ok=True)
    back = f"- [[Imported/ChatGPT/{note_id}]]\n"
    for topic in topics:
        tp = TOPIC_DIR / f"{topic}.md"
        if tp.exists():
            with tp.open("a", encoding="utf-8") as f:
                f.write(back)
        else:
            tp.write_text(f"# {topic}\n\n{back}", encoding="utf-8")

    return True


def main():
    md_files = sorted(CHATGPT_DIR.glob("ChatGPT_*.md"))
    if not md_files:
        print(f"No ChatGPT_*.md files found in {CHATGPT_DIR}")
        sys.exit(1)

    print(f"Found {len(md_files)} files in {CHATGPT_DIR}")
    print(f"Importing to {OUT_DIR}\n")

    imported, skipped = 0, 0
    for f in md_files:
        turns = parse_md(f)
        if not turns:
            skipped += 1
            continue

        ts      = ts_from_filename(f)
        note_id = ts.strftime("%Y-%m-%d_%H-%M-%S") + f"_{imported}"
        title   = next((t["content"][:60] for t in turns if t["role"] == "user"), f.stem)

        if write_note(note_id, title, turns, ts):
            imported += 1
        else:
            skipped += 1

    print(f"\nObsidian: {imported} notes written, {skipped} skipped (duplicates)")

    # Also index the clean Obsidian notes into the vector store for ARIA context
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from agent_core.memory_vector import VectorMemory
        vm = VectorMemory()
        if vm.is_available:
            print(f"\nIndexing into vector store...")
            result = vm.index_path(str(OUT_DIR), recursive=False)
            print(f"Vector store: {result['indexed']} indexed, {result['skipped']} skipped")
        else:
            print("\nVector store not available — run memory server first, then it will index on startup.")
    except Exception as e:
        print(f"\nVector store skipped ({e}) — will be indexed on next memory server startup.")

    print(f"\nDone. ARIA will have full context from your ChatGPT conversations.")


if __name__ == "__main__":
    main()
