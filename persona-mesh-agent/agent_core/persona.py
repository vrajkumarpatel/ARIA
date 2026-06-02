from typing import Dict
from .config import config

PERSONAS: Dict[str, Dict] = {
    "Assistant": {
        "tone":   "helpful, warm, clear",
        "style":  "conversational and supportive",
        "traits": ["empathetic", "direct", "concise"],
        "prefix": "You are a helpful, warm, and thoughtful AI assistant.",
    },
    "Technical": {
        "tone":   "precise, analytical, structured",
        "style":  "detailed technical explanations with examples",
        "traits": ["methodical", "accurate", "comprehensive"],
        "prefix": "You are a precise technical expert who gives structured, accurate explanations.",
    },
    "Creative": {
        "tone":   "imaginative, expressive, fluid",
        "style":  "narrative-driven with vivid language",
        "traits": ["inventive", "metaphorical", "explorative"],
        "prefix": "You are a creative thinker who brings imagination and vivid language to every response.",
    },
    "Socratic": {
        "tone":   "inquisitive, reflective, challenging",
        "style":  "questions that deepen understanding",
        "traits": ["curious", "probing", "philosophical"],
        "prefix": "You are a Socratic guide who helps users discover insights through thoughtful questions.",
    },
}


class PersonaEngine:
    """
    STATELESS persona layer.
    ─────────────────────────────────────────────────────────────
    ✅ Modifies tone and style only.
    ❌ Never stores memory.
    ❌ Never retrieves data.
    ─────────────────────────────────────────────────────────────
    Accepts structured context injected from outside; returns a
    styled system prompt. No side effects.
    """

    def __init__(self, persona_name: str = None):
        name = (persona_name or config.PERSONA_NAME).title()
        self.persona_name = name if name in PERSONAS else "Assistant"
        self._p = PERSONAS[self.persona_name]

    # ── Public API ────────────────────────────────────────────

    def get_system_prompt(self, context: Dict = None) -> str:
        """Build a complete system prompt. Pure function — no I/O."""
        memory_block = ""
        if context and context.get("combined_context"):
            memory_block = (
                "\n\n--- MEMORY CONTEXT (use this; never hallucinate beyond it) ---\n"
                f"{context['combined_context']}\n"
                "--- END MEMORY CONTEXT ---"
            )

        return (
            f"{self._p['prefix']}\n\n"
            f"TONE:   {self._p['tone']}\n"
            f"STYLE:  {self._p['style']}\n"
            f"TRAITS: {', '.join(self._p['traits'])}\n\n"
            "RULES:\n"
            "- ONLY reference the memory context provided above.\n"
            "- Never fabricate facts not present in the context.\n"
            "- If no relevant memory exists, say so naturally.\n"
            "- Keep responses focused and token-efficient."
            f"{memory_block}"
        )

    def apply_tone(self, text: str) -> str:
        """Lightweight stateless tone pass — strips extra whitespace."""
        return text.strip()

    @property
    def name(self) -> str:
        return self.persona_name

    @staticmethod
    def list_personas():
        return list(PERSONAS.keys())
