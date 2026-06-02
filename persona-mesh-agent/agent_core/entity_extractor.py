"""
Named entity extraction via spaCy.
Enriches stored conversation turns with structured facts.
"""

from typing import List, Dict

try:
    import spacy
    try:
        _nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        SPACY_AVAILABLE = False
        _nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    _nlp = None

# Entity types worth storing as memory facts
_KEEP = {"PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "DATE", "WORK_OF_ART", "LAW", "LANGUAGE"}

# Generic noise entities to ignore
_NOISE = {"aria", "user", "you", "i", "me", "we", "it", "they"}


def extract_entities(text: str) -> List[Dict]:
    """Return list of {text, type} dicts from *text*. Empty list if spaCy unavailable."""
    if not SPACY_AVAILABLE or not _nlp:
        return []
    doc = _nlp(text[:1500])
    seen, results = set(), []
    for ent in doc.ents:
        norm = ent.text.strip()
        if (ent.label_ in _KEEP
                and norm.lower() not in _NOISE
                and norm not in seen
                and len(norm) > 1):
            seen.add(norm)
            results.append({"text": norm, "type": ent.label_})
    return results


def entities_to_line(entities: List[Dict]) -> str:
    """Format entities as a compact metadata line for Obsidian notes."""
    if not entities:
        return ""
    parts = [f"{e['text']} ({e['type']})" for e in entities]
    return "**Entities:** " + " · ".join(parts)
