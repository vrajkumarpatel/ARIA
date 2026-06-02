#!/usr/bin/env python3
"""
AI Chat History Importer → Obsidian Memory Vault
=================================================
Imports conversations from ChatGPT, Claude, and Gemini exports
into ARIA's Obsidian memory vault as searchable markdown notes.

Usage:
  python import_chats.py --chatgpt  conversations.json
  python import_chats.py --claude   claude_conversations.json
  python import_chats.py --gemini   Takeout/Gemini/
  python import_chats.py --all      (auto-detect files in current dir)

Export instructions:
  ChatGPT : Settings → Data Controls → Export Data → conversations.json
  Claude  : Settings → Account → Export Data → conversations.json
  Gemini  : takeout.google.com → select "Gemini Apps" → download
"""

import json
import argparse
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

VAULT = Path(r"C:\ARIA\ARIA-Memory-Vault")
IMPORT_DIR = VAULT / "Imported"

STOP = {"the","and","for","are","but","not","you","all","can","was","with",
        "this","that","have","from","they","will","been","were","your","just",
        "about","what","how","its","more","also","been","when","would","could",
        "should","than","then","these","those","their","there","which","while"}


# ── Shared helpers ────────────────────────────────────────────────────────────

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


def write_note(folder: Path, note_id: str, title: str,
               turns: list[dict], source: str, ts: datetime):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{note_id}.md"
    if path.exists():
        return  # skip duplicates

    # Build body
    body_parts = [
        f"---",
        f"source: {source}",
        f"timestamp: {ts.isoformat()}",
        f"title: {title[:80]}",
        f"---",
        f"",
        f"# {title[:80]}",
        f"",
    ]

    full_text = ""
    for turn in turns:
        role = turn.get("role", "unknown")
        content = turn.get("content", "").strip()
        if not content:
            continue
        label = "**You:**" if role == "user" else f"**{source}:**"
        body_parts.append(f"{label} {content[:500]}")
        body_parts.append("")
        full_text += content + " "

    topics = extract_topics(full_text)
    if topics:
        topic_links = "  ".join(f"[[Imported-Topics/{t}]]" for t in topics)
        body_parts += ["## Topics", topic_links, ""]

    path.write_text("\n".join(body_parts), encoding="utf-8")

    # Upsert topic nodes
    topic_dir = VAULT / "Imported-Topics"
    topic_dir.mkdir(exist_ok=True)
    back = f"- [[Imported/{source}/{note_id}]]\n"
    for topic in topics:
        tp = topic_dir / f"{topic}.md"
        if tp.exists():
            tp.open("a", encoding="utf-8").write(back)
        else:
            tp.write_text(f"# {topic}\n\n{back}", encoding="utf-8")

    return path


# ── ChatGPT importer ──────────────────────────────────────────────────────────

def import_chatgpt(file_path: Path) -> int:
    print(f"\n[ChatGPT] Reading {file_path.name}...")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    folder = IMPORT_DIR / "ChatGPT"
    count = 0

    for conv in data:
        try:
            title     = conv.get("title", "Untitled")
            create_ts = conv.get("create_time", 0)
            ts        = datetime.fromtimestamp(create_ts, tz=timezone.utc)
            note_id   = ts.strftime("%Y-%m-%d_%H-%M-%S") + f"_{count}"

            # Extract messages from mapping tree
            mapping = conv.get("mapping", {})
            turns   = []
            for node in mapping.values():
                msg = node.get("message")
                if not msg:
                    continue
                role    = msg.get("author", {}).get("role", "")
                content = msg.get("content", {})
                parts   = content.get("parts", []) if isinstance(content, dict) else []
                text    = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
                if text and role in ("user", "assistant"):
                    turns.append({"role": role, "content": text})

            if turns:
                write_note(folder, note_id, title, turns, "ChatGPT", ts)
                count += 1
        except Exception as e:
            print(f"  skip: {e}")

    print(f"  [ChatGPT] Imported {count} conversations")
    return count


# ── Claude importer ───────────────────────────────────────────────────────────

def import_claude(file_path: Path) -> int:
    print(f"\n[Claude] Reading {file_path.name}...")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    folder = IMPORT_DIR / "Claude"
    count  = 0

    # Claude export: list of conversations
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict):
        conversations = data.get("conversations", [data])
    else:
        print("  [Claude] Unrecognised format")
        return 0

    for conv in conversations:
        try:
            title     = conv.get("name", conv.get("title", "Untitled"))
            created   = conv.get("created_at", conv.get("create_time", ""))
            try:
                ts = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(tz=timezone.utc)

            note_id = ts.strftime("%Y-%m-%d_%H-%M-%S") + f"_{count}"

            # Handle both chat_messages and messages formats
            raw_turns = conv.get("chat_messages",
                        conv.get("messages", []))
            turns = []
            for m in raw_turns:
                role = m.get("sender", m.get("role", ""))
                # Claude uses "human"/"assistant"
                role = "user" if role in ("human", "user") else "assistant"
                content = m.get("text", m.get("content", ""))
                if isinstance(content, list):
                    content = " ".join(
                        c.get("text", "") if isinstance(c, dict) else str(c)
                        for c in content
                    )
                if str(content).strip():
                    turns.append({"role": role, "content": str(content).strip()})

            if turns:
                write_note(folder, note_id, title, turns, "Claude", ts)
                count += 1
        except Exception as e:
            print(f"  skip: {e}")

    print(f"  [Claude] Imported {count} conversations")
    return count


# ── Gemini importer ───────────────────────────────────────────────────────────

def import_gemini(path: Path) -> int:
    print(f"\n[Gemini] Reading from {path}...")
    count = 0
    folder = IMPORT_DIR / "Gemini"

    # Gemini Takeout exports as JSON files in a folder
    json_files = list(path.rglob("*.json")) if path.is_dir() else [path]

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))

            # Gemini format varies — try common structures
            convs = []
            if isinstance(data, list):
                convs = data
            elif isinstance(data, dict):
                convs = (data.get("conversations")
                      or data.get("messages")
                      or [data])

            for conv in convs:
                title = conv.get("title", jf.stem)
                msgs  = conv.get("messages", conv.get("turns", []))
                ts    = datetime.now(tz=timezone.utc)
                note_id = f"gemini_{count}"
                turns = []

                for m in msgs:
                    role    = m.get("author", m.get("role", ""))
                    role    = "user" if role in ("user", "human", "0") else "assistant"
                    content = m.get("content", m.get("text", ""))
                    if isinstance(content, list):
                        content = " ".join(
                            p.get("text", str(p)) if isinstance(p, dict) else str(p)
                            for p in content
                        )
                    if str(content).strip():
                        turns.append({"role": role, "content": str(content).strip()})

                if turns:
                    write_note(folder, note_id, title, turns, "Gemini", ts)
                    count += 1
        except Exception as e:
            print(f"  skip {jf.name}: {e}")

    print(f"  [Gemini] Imported {count} conversations")
    return count


# ── Auto-detect ───────────────────────────────────────────────────────────────

def auto_detect() -> int:
    total = 0
    cwd   = Path(".")

    for f in cwd.rglob("conversations.json"):
        text = f.read_text(encoding="utf-8", errors="ignore")[:500]
        if "mapping" in text:
            total += import_chatgpt(f)
        elif "chat_messages" in text or '"sender"' in text:
            total += import_claude(f)

    for f in cwd.rglob("*.json"):
        if f.name == "conversations.json":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")[:200]
        if "gemini" in f.name.lower() or "bard" in f.name.lower():
            total += import_gemini(f)

    return total


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import AI chats into Obsidian")
    parser.add_argument("--chatgpt", metavar="FILE",  help="ChatGPT conversations.json")
    parser.add_argument("--claude",  metavar="FILE",  help="Claude conversations.json")
    parser.add_argument("--gemini",  metavar="PATH",  help="Gemini export folder or file")
    parser.add_argument("--all",     action="store_true", help="Auto-detect in current dir")
    args = parser.parse_args()

    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Vault: {VAULT}")

    total = 0
    if args.chatgpt:
        total += import_chatgpt(Path(args.chatgpt))
    if args.claude:
        total += import_claude(Path(args.claude))
    if args.gemini:
        total += import_gemini(Path(args.gemini))
    if args.all or total == 0:
        total += auto_detect()

    print(f"\nDone. {total} conversations imported to {IMPORT_DIR}")
    print("Open Obsidian Graph View (Ctrl+G) to see the memory network.")


if __name__ == "__main__":
    main()
