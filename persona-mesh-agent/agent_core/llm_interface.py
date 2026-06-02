import random
from typing import List, Dict

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .config import config

_MOCK_RESPONSES = [
    "That's a great point. Based on the context available to me, I'd suggest thinking carefully about your goals first.",
    "I don't have specific memory about that yet — but I'm here to reason through it with you.",
    "From what I recall in our previous exchanges, this connects to something you mentioned earlier.",
    "Interesting question. Let me reason through this with the context I have.",
    "I want to make sure I'm being accurate — based on what's in my memory context, here's my take:",
]


class LLMInterface:
    """
    Stateless response generator.
    ─────────────────────────────────────────────────────────────
    - Accepts context + system prompt + conversation history.
    - Calls OpenAI-compatible API.
    - Falls back to canned mock responses if no API key.
    ─────────────────────────────────────────────────────────────
    """

    MAX_HISTORY_TURNS = 6  # recent turns to include in prompt

    def __init__(self):
        self._client = None
        self._available = False

        if OPENAI_AVAILABLE and config.OPENAI_API_KEY:
            try:
                kwargs: Dict = {"api_key": config.OPENAI_API_KEY}
                if config.OPENAI_BASE_URL:
                    kwargs["base_url"] = config.OPENAI_BASE_URL
                self._client = OpenAI(**kwargs)
                self._available = True
            except Exception as e:
                print(f"  [LLM] Client init failed: {e} — mock mode active")

    # ── Public API ────────────────────────────────────────────

    def generate_response(
        self,
        user_input: str,
        context: Dict,
        system_prompt: str,
        conversation_history: List[Dict] = None,
    ) -> str:
        if not self._available:
            return self._mock(user_input, context)

        messages = [{"role": "system", "content": system_prompt}]

        # Inject recent conversation turns (sliding window)
        for turn in (conversation_history or [])[-self.MAX_HISTORY_TURNS:]:
            messages.append({"role": "user",      "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})

        messages.append({"role": "user", "content": user_input})

        try:
            resp = self._client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [LLM] Generation failed: {e}")
            return self._mock(user_input, context)

    @property
    def is_available(self) -> bool:
        return self._available

    # ── Internal ──────────────────────────────────────────────

    def _mock(self, user_input: str, context: Dict) -> str:
        base    = random.choice(_MOCK_RESPONSES)
        summary = context.get("summary", "")
        if summary and "No prior" not in summary:
            return f"{base}\n\n[Memory: {summary}]"
        return base
