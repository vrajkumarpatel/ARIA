import re
from pathlib import Path

import sys

VAULT = Path(r"C:\ARIA\ARIA-Memory-Vault")
folder = sys.argv[1] if len(sys.argv) > 1 else "ChatGPT"
CHATGPT_DIR = VAULT / "Imported" / folder
TOPIC_DIR = VAULT / "Imported-Topics"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


def get_title(path):
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("title:"):
                return line.split(":", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


notes = list(CHATGPT_DIR.glob("*.md"))
print(f"Found {len(notes)} notes to rename")

renamed, skipped = 0, 0
rename_map = {}

for note in sorted(notes):
    title = get_title(note)
    if not title:
        skipped += 1
        continue

    slug = slugify(title)
    if not slug:
        skipped += 1
        continue

    new_path = CHATGPT_DIR / f"{slug}.md"
    counter = 1
    while new_path.exists() and new_path != note:
        new_path = CHATGPT_DIR / f"{slug}-{counter}.md"
        counter += 1

    if new_path == note:
        skipped += 1
        continue

    rename_map[note.stem] = new_path.stem
    note.rename(new_path)
    renamed += 1

print(f"Renamed: {renamed}  Skipped: {skipped}")

if rename_map and TOPIC_DIR.exists():
    updated = 0
    for tf in TOPIC_DIR.glob("*.md"):
        try:
            content = tf.read_text(encoding="utf-8", errors="ignore")
            new_content = content
            for old, new in rename_map.items():
                new_content = new_content.replace(
                    f"[[Imported/{folder}/{old}]]",
                    f"[[Imported/{folder}/{new}]]"
                )
            if new_content != content:
                tf.write_text(new_content, encoding="utf-8")
                updated += 1
        except Exception:
            pass
    print(f"Updated backlinks in {updated} topic files")

print("Done.")
