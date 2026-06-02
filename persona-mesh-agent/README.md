# 🧠 ARIA — Memory Agent

> *"It remembers everything, but only thinks about what matters."*

**Author:** Vrajkumar Patel — NLU Senior, AI Concentration

## Architecture

```
User Input
   ↓
Memory Retrieval (parallel)
   ├── LlamaIndex  →  semantic recall
   └── Neo4j       →  relationship graph
   ↓
ContextBuilder  →  deduplicate + rank + compress (≤2000 tokens)
   ↓
PersonaEngine   →  style system prompt (STATELESS)
   ↓
LLM             →  generate response
   ↓
Memory Storage  →  vector + graph
```

## Quick Start

```bash
cd persona-mesh-agent
cp .env.example .env
# Fill in your API key(s) in .env

pip install -r requirements.txt
python agent.py
```

Works with **no API keys** — falls back to mock LLM + in-memory stores.

## Neo4j (optional — graph memory + visualization)

```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

Then open `http://localhost:7474` to visualize the memory graph.

## CLI Commands

| Command | Effect |
|---|---|
| `/persona Technical` | Switch to Technical persona |
| `/personas` | List all personas |
| `/status` | Show component health |
| `/clear` | Clear conversation history |
| `exit` / `quit` | Quit |

## Personas

| Name | Tone |
|---|---|
| `Assistant` | Warm, clear, helpful (default) |
| `Technical` | Precise, structured, analytical |
| `Creative` | Imaginative, narrative, fluid |
| `Socratic` | Questioning, philosophical, probing |

Switch instantly with `/persona <name>` — PersonaEngine is stateless,
no memory is affected.

## Drop documents into `/data`

Add `.txt` or `.md` files to `./data/` before running.
LlamaIndex will index them on first launch and persist the index.
The agent will recall relevant passages automatically.

## Design Principles

| Rule | Implementation |
|---|---|
| PersonaEngine is stateless | Never touches storage; pure prompt builder |
| Selective recall | Only top-K relevant chunks retrieved per turn |
| Token budget | Hard cap at `MAX_CONTEXT_TOKENS` (default 2000) |
| No hallucination | System prompt explicitly forbids making up facts |
| Deduplication | Jaccard similarity removes near-duplicate chunks |
| Graceful degradation | All components have offline fallbacks |
