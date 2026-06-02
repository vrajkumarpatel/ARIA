#!/usr/bin/env python3
"""
One-shot script: clean existing Obsidian vault notes.
  - Strips [User] / [user] prefix from **User:** lines
  - Strips [EMOTION:...] tags from **ARIA:** lines
Run once, then delete.
"""

import re
from pathlib import Path

VAULT = Path(r"C:\ARIA\ARIA-Memory-Vault")
USER_PREFIX = re.compile(r"(\*\*(?:User|You):\*\*\s*)\[User\]\s*", re.IGNORECASE)
EMOTION_TAG = re.compile(r"\[EMOTION:[^\]]*\]")

fixed = 0
for md in VAULT.rglob("*.md"):
    if ".obsidian" in md.parts or "Imported" in md.parts:
        continue
    original = md.read_text(encoding="utf-8", errors="ignore")
    cleaned  = USER_PREFIX.sub(r"\1", original)
    cleaned  = EMOTION_TAG.sub("", cleaned)
    # Collapse multiple spaces left by tag removal
    cleaned  = re.sub(r"  +", " ", cleaned)
    if cleaned != original:
        md.write_text(cleaned, encoding="utf-8")
        fixed += 1
        print(f"  cleaned: {md.name}")

print(f"\nDone. {fixed} notes cleaned.")
