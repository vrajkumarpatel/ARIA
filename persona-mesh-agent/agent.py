#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║              🧠  ARIA — Memory Agent                 ║
║   Infinite memory. Selective recall. Zero waste.     ║
╚══════════════════════════════════════════════════════╝

Author: Vrajkumar Patel
Run:  python agent.py
"""

import sys
import signal
from typing import List, Dict

from agent_core import (
    PersonaEngine,
    VectorMemory,
    GraphMemory,
    ContextBuilder,
    LLMInterface,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner():
    print("""
╔══════════════════════════════════════════════════════╗
║              🧠  ARIA — Memory Agent                 ║
║   Infinite memory. Selective recall. Zero waste.     ║
╚══════════════════════════════════════════════════════╝""")


def _status(persona, vector_mem, graph_mem, llm):
    v = "✅ LlamaIndex"  if vector_mem.is_available else "⚠️  mock-vector"
    g = "✅ Neo4j"       if graph_mem.is_available  else "⚠️  in-memory"
    l = "✅ LLM"         if llm.is_available        else "⚠️  mock-LLM"
    print(f"\n  Persona: {persona.name}  │  {v}  │  {g}  │  {l}\n")


def _help():
    print(
        "\n  Commands:\n"
        "    /status            — show component status\n"
        "    /persona <name>    — switch persona\n"
        "    /personas          — list available personas\n"
        "    /clear             — clear conversation history\n"
        "    exit | quit        — quit\n"
    )


# ── Pipeline steps ────────────────────────────────────────────────────────────

def _retrieve_context(
    user_input: str,
    vector_mem: VectorMemory,
    graph_mem: GraphMemory,
    builder: ContextBuilder,
    history: List[Dict],
) -> Dict:
    vector_results = vector_mem.query(user_input)
    graph_results  = graph_mem.get_related_nodes(user_input)
    return builder.build(user_input, vector_results, graph_results, history)


def _store(
    user_input: str,
    response: str,
    context: Dict,
    vector_mem: VectorMemory,
    graph_mem: GraphMemory,
):
    text = f"User: {user_input}\nAgent: {response}"
    vector_mem.store(text, {"type": "conversation"})
    graph_mem.store_interaction(user_input, response, context)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _banner()
    print("\nInitializing …")

    persona    = PersonaEngine()
    vector_mem = VectorMemory()
    graph_mem  = GraphMemory()
    builder    = ContextBuilder()
    llm        = LLMInterface()

    _status(persona, vector_mem, graph_mem, llm)

    history: List[Dict] = []

    def _shutdown(sig=None, frame=None):
        print("\n\nShutting down. Goodbye.")
        graph_mem.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)

    print('  Type a message, or "/help" for commands.')
    print("  " + "─" * 52)

    while True:
        try:
            raw = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            _shutdown()

        if not raw:
            continue

        # ── Built-in commands ──────────────────────────────────
        low = raw.lower()

        if low in ("exit", "quit"):
            _shutdown()

        if low == "/help":
            _help()
            continue

        if low == "/status":
            _status(persona, vector_mem, graph_mem, llm)
            continue

        if low == "/personas":
            print(f"  Available: {', '.join(PersonaEngine.list_personas())}")
            continue

        if low == "/clear":
            history.clear()
            print("  Conversation history cleared.")
            continue

        if low.startswith("/persona "):
            name = raw[9:].strip().title()
            if name in PersonaEngine.list_personas():
                persona = PersonaEngine(name)
                print(f"  ↳ Switched to {name} persona.")
            else:
                print(f"  ↳ Unknown persona. Try: {', '.join(PersonaEngine.list_personas())}")
            continue

        # ── Main pipeline ──────────────────────────────────────

        # 1. Retrieve relevant memory (vector + graph, parallel in spirit)
        context = _retrieve_context(raw, vector_mem, graph_mem, builder, history)

        # 2. Persona styles the system prompt (stateless)
        system_prompt = persona.get_system_prompt(context)

        # 3. Generate response
        response = llm.generate_response(
            user_input=raw,
            context=context,
            system_prompt=system_prompt,
            conversation_history=history,
        )
        response = persona.apply_tone(response)

        # 4. Display
        src_tag = f" [{', '.join(context['sources'])}]" if context.get("sources") else ""
        print(f"\nAgent{src_tag}: {response}")

        # 5. Store to both memory layers
        _store(raw, response, context, vector_mem, graph_mem)

        # 6. Update conversation history
        history.append({"user": raw, "assistant": response})


if __name__ == "__main__":
    main()
