# ARIA — Adaptive Responsive Intelligent Agent

<div align="center">

**🥇 1st Place — NLU AI Senior Capstone Showcase, May 2026**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-0.10+-purple?style=flat)](https://llamaindex.ai)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.14+-008CC1?style=flat&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=flat)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*An emotionally intelligent AI study companion with persistent long-term memory, real-time voice I/O, and a Live2D animated avatar — built as an NLU senior capstone and awarded 1st place by the faculty panel.*

</div>

---

## What is ARIA?

Most AI tools start every session blank. ARIA doesn't.

ARIA is a **real-time AI companion** that listens to you, remembers your full academic and personal history across every session, and responds through a Live2D animated avatar with synchronized voice and emotion-driven facial expressions. She was built as an answer to a specific design question: *can AI be structured to guide learning rather than bypass it?*

She refuses to do your homework. She asks what you understand first. And she remembers everything you've ever told her.

**End-to-end latency: ~4–5 seconds** from when you stop speaking to when ARIA starts responding.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ARIA System                                │
│                                                                     │
│  You speak                                                          │
│      │                                                              │
│      ▼                                                              │
│  Whisper STT  (~350ms)                                              │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────┐           │
│  │              ARIA Memory Proxy  (Python/FastAPI)     │           │
│  │                                                      │           │
│  │  ┌──────────────────┐   ┌──────────────────────┐    │           │
│  │  │  Obsidian Vault  │   │  LlamaIndex Vector   │    │           │
│  │  │  BM25 Search     │   │  HuggingFace Embed   │    │           │
│  │  └────────┬─────────┘   └──────────┬───────────┘    │           │
│  │           │                        │                 │           │
│  │           └──────────┬─────────────┘                 │           │
│  │                      ▼                               │           │
│  │             ContextBuilder                           │           │
│  │         (deduplicate → rank → compress)              │           │
│  │                      │                               │           │
│  │                      ▼                               │           │
│  │         Inject memory into user message              │           │
│  └──────────────────────┬──────────────────────────────┘           │
│                         │                                           │
│                         ▼                                           │
│             Groq Cloud API  (llama-3.3-70b, ~3000ms)               │
│                         │                                           │
│                         ▼                                           │
│  ┌──────────────────────────────────────────────────┐              │
│  │           PersonaEngine (C# / .NET)              │              │
│  │                                                  │              │
│  │  Token stream → Emotion processor                │              │
│  │      [EMOTION:😊] tags → Live2D expressions      │              │
│  │                                                  │              │
│  │  Clean text → ElevenLabs TTS                     │              │
│  │      Audio → NVIDIA Audio2Face lip-sync          │              │
│  │                         │                        │              │
│  │                         ▼                        │              │
│  │              Live2D Avatar (1080×1920)            │              │
│  └──────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **LLM** | Groq API — Llama 3.3 70B | Language model inference |
| **Memory — Semantic** | LlamaIndex + HuggingFace all-MiniLM-L6-v2 | Vector embeddings, RAG retrieval |
| **Memory — Graph** | Neo4j Aura | Relationship mesh, entity linking |
| **Memory — Episodic** | Obsidian Markdown Vault + BM25 | Long-term conversation storage |
| **API Layer** | FastAPI + Uvicorn | Async REST + WebSocket server |
| **LLM Proxy** | Custom Python proxy (httpx) | Memory injection, rate limiting, streaming |
| **NLP** | spaCy en_core_web_sm | Named entity recognition |
| **Token counting** | tiktoken cl100k_base | Token budget enforcement |
| **Avatar** | Live2D Cubism | Animated 2D character (17 emotions) |
| **Lip Sync** | NVIDIA Audio2Face | Neural audio-to-blendshape inference |
| **TTS** | ElevenLabs Turbo v2.5 | Custom voice synthesis |
| **STT** | Whisper (via PersonaEngine) | Real-time speech recognition |
| **Calendar** | Google Calendar API (OAuth2) | Schedule context injection |
| **Runtime** | Python 3.11, C# / .NET 8 | Backend + engine |

---

## Features

- **Persistent long-term memory** — every conversation turn saved, indexed, and recalled via hybrid BM25 + vector search (RAG pipeline)
- **Cross-platform memory import** — import full conversation history from ChatGPT, Claude, Gemini; ARIA inherits all of it
- **Real-time emotion-driven avatar** — 17 emotion states generated live from LLM output, synchronized with audio via Audio2Face
- **Voice I/O** — full duplex: Whisper STT input, ElevenLabs TTS output, ~350ms transcription latency
- **Pedagogical personality** — refuses to answer directly; guides users to their own understanding via Socratic dialogue
- **Google Calendar integration** — upcoming events injected as context so ARIA knows your schedule
- **WebSocket graph push** — Neo4j memory graph streamed live to connected clients on every store
- **File auto-indexing** — watchdog monitors directories and re-indexes on file changes
- **Graceful degradation** — every component (vector store, graph DB, LLM) has an offline fallback; system always runs

---

## The Technical Challenges

### 1. Memory Injection Without Breaking Streaming Latency

**The problem:** Injecting retrieved memory context into each LLM request adds a lookup round-trip before the Groq call. Doing this naively would stall the voice pipeline.

**The solution:** The proxy intercepts the request, performs BM25 search over the Obsidian vault and vector query in parallel, compresses the result to a hard token budget (`MAX_CONTEXT_TOKENS = 2000`), then injects it directly into the last user message — not the system prompt. This keeps the injection path transparent to PersonaEngine and adds under 50ms to the pre-LLM phase.

The `ContextBuilder` runs deduplication (Jaccard similarity ≥ 0.70 threshold), relevance ranking by keyword overlap, and a tiktoken-accurate compression pass before injection.

---

### 2. Groq Rate Limiting Under Real-Time Conversation

**The problem:** Groq's free tier enforces a hard 30 RPM limit. Under live conversation conditions with a user speaking continuously, back-to-back requests would exceed this and return 429s mid-sentence.

**The solution:** A centralized async rate limiter (`_groq_throttle`) enforces a minimum 2.1-second gap between Groq calls using an `asyncio.Lock`. The streaming path also implements a 3-attempt retry with exponential backoff on 429 responses. Error states yield a silent empty chunk rather than crashing the stream so the avatar never freezes.

---

### 3. Embedding Model Portability (No API Key Required)

**The problem:** OpenAI's embedding API costs money and requires a key. The system needed to work with zero credentials for demos and development.

**The solution:** The vector memory stack uses a priority chain: HuggingFace `all-MiniLM-L6-v2` (local, no key, 384-dim) → OpenAI `text-embedding-3-small` (if key provided) → keyword mock. The embedding model tag is persisted to `.model_tag`; if the model changes between runs, the index is automatically invalidated and rebuilt to avoid silent embedding mismatches.

---

### 4. CUDA Resource Conflicts Across Multi-Model GPU Inference

**The problem:** Running Whisper STT, Qwen3 TTS, Audio2Face lip-sync, and the LlamaIndex embedding model simultaneously caused ONNX Runtime initialization stalls of 20–30 seconds on the first inference call. The root cause was cuDNN version conflicts — cuDNN 9.6 introduced breaking changes to memory pool allocation that affected Audio2Face's ONNX session.

**The solution:** Reverted to cuDNN 9.1.1 for the Audio2Face ONNX runtime. The Qwen3 TTS pipeline was patched to use direct audio streaming (CTC bypass) rather than word-by-word generation, eliminating the main stall point. The LLM inference was moved off-device to Groq cloud entirely to remove GPU contention between the language model and the audio/vision stack.

---

### 5. Cross-Platform Conversation Import and Deduplication

**The problem:** ChatGPT exports use a non-standard Markdown format with HTML-tagged response blocks and horizontal rule separators. Importing these naively created duplicate entries when the same export was run twice, and imported HTML tags leaked into ARIA's memory context.

**The solution:** The import pipeline (`import_chatgpt_md.py`) parses the `# User / # ChatGPT` block format with separator regex, strips HTML tags, generates a deterministic note ID from the export timestamp, and skips existing notes by ID. A post-import cleanup script (`clean_vault.py`) strips `[User]` prefixes and `[EMOTION:...]` tags from previously imported notes.

---

### 6. Live Emotion Synchronization with Streaming Text

**The problem:** The LLM was instructed to embed `[EMOTION:😊]` tags inline with its response. These tags had to be extracted in real time as tokens streamed in — before reaching TTS — without introducing audio delay or having the tags read aloud.

**The solution:** The streaming response is collected token-by-token in the proxy. A regex processor (`_EMOTION_TAG`) strips tags from the stored text before writing to memory. On the PersonaEngine side, an `EmotionProcessor` service reads the raw token stream, extracts timestamped emotion events, and fires them against the Live2D animation rig in sync with the audio playback position. The avatar's expressions change mid-sentence in response to what the LLM is generating — not pre-scripted.

---

## Project Structure

```
ARIA/
├── persona-mesh-agent/          # Python backend — all original code
│   ├── llm_proxy.py             # LLM memory proxy (main entry point for ARIA)
│   ├── api_server.py            # REST API bridge (simple, no WebSocket)
│   ├── memory_websocket_server.py  # REST + WebSocket combined server
│   ├── agent.py                 # CLI chat interface (dev/testing)
│   ├── import_chatgpt_md.py     # ChatGPT conversation importer
│   ├── clean_vault.py           # Vault cleanup utility
│   ├── requirements.txt
│   ├── .env.example
│   └── agent_core/
│       ├── config.py            # All env-var config
│       ├── llm_interface.py     # OpenAI-compatible LLM client
│       ├── persona.py           # Stateless persona/prompt engine
│       ├── context_builder.py   # RAG pipeline: dedup → rank → compress
│       ├── memory_vector.py     # LlamaIndex vector store
│       ├── memory_graph.py      # Neo4j graph memory
│       ├── memory_obsidian.py   # Obsidian vault store + BM25 search
│       ├── entity_extractor.py  # spaCy NER
│       ├── calendar_fetcher.py  # Google Calendar OAuth2 integration
│       └── __init__.py
├── config/
│   └── appsettings.example.json  # PersonaEngine config template (keys redacted)
├── docs/
│   └── ARIA-Presentation-Guide.md  # Full showcase script + judge Q&A
└── .gitignore
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- [PersonaEngine 3.0.2](https://github.com/fagenorn/handcrafted-persona-engine) (Windows only, for avatar + voice)
- Groq API key (free tier works)
- Optional: Neo4j Aura account (free tier), ElevenLabs API key

### 1. Clone and install

```bash
git clone https://github.com/vrajkumarpatel/ARIA.git
cd ARIA/persona-mesh-agent
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env:
#   OPENAI_API_KEY=your_groq_key
#   OPENAI_BASE_URL=https://api.groq.com/openai/v1
#   LLM_MODEL=llama-3.3-70b-versatile
```

### 3. Run the memory proxy

```bash
python llm_proxy.py
# Listening on http://localhost:7777/v1
```

### 4. Configure PersonaEngine

Copy `config/appsettings.example.json` → your PersonaEngine directory as `appsettings.json`.  
Set `TextEndpoint` to `http://localhost:7777/v1` and fill in your API keys.

### 5. (Optional) Import your ChatGPT history

```bash
# Place ChatGPT export .md files in C:\CHATGPT\
python import_chatgpt_md.py
```

### 6. (Optional) Google Calendar

```bash
# Download credentials.json from Google Cloud Console → OAuth 2.0 Client
python -c "from agent_core.calendar_fetcher import authenticate; authenticate()"
```

---

## API Reference

All endpoints served on `http://localhost:7777` (proxy) or `http://localhost:8765` (memory server).

### Memory Proxy (`llm_proxy.py`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | OpenAI-compatible endpoint — memory-injected, rate-limited, streaming |
| `GET` | `/v1/models` | Model list (for PersonaEngine compatibility) |
| `GET` | `/health` | Liveness check + memory stats |

### Memory Server (`memory_websocket_server.py`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/context` | Query memory for a user input — returns RAG context |
| `POST` | `/api/store` | Persist a conversation turn to all memory layers |
| `POST` | `/api/index-files` | Index a file or directory into vector memory |
| `GET` | `/api/graph` | Pull current Neo4j graph snapshot |
| `GET` | `/api/stats` | Memory statistics |
| `GET` | `/health` | Liveness + component status |
| `WS` | `ws://localhost:8766` | Live graph push on every memory store |

### Context Query Request/Response

```json
POST /api/context
{
  "user_input": "what did I say about backpropagation?",
  "top_k": 3
}

→ {
  "combined_context": "...",
  "summary": "3 chunk(s) retrieved — query: what did I say...",
  "sources": ["LlamaIndex", "Obsidian"],
  "semantic_memory": "...",
  "graph_memory": "..."
}
```

---

## Memory System Design

ARIA uses a **three-layer hybrid memory architecture**:

```
┌──────────────────────────────────────────────────────┐
│  Layer 1 — Episodic (Obsidian Vault)                 │
│  Every conversation turn → timestamped .md note      │
│  Search: BM25Okapi keyword ranking                   │
│  Human-readable, visualizable in Obsidian Graph View │
├──────────────────────────────────────────────────────┤
│  Layer 2 — Semantic (LlamaIndex + HuggingFace)       │
│  Conversation + document chunks → vector embeddings  │
│  Search: cosine similarity retrieval (top-k)         │
│  Persisted to disk, survives restarts                │
├──────────────────────────────────────────────────────┤
│  Layer 3 — Relational (Neo4j Graph)                  │
│  UserInput → [:GENERATED] → Response nodes          │
│  UserInput → [:MENTIONS] → Entity nodes              │
│  Enables relationship traversal + entity memory      │
└──────────────────────────────────────────────────────┘
         ↓
  ContextBuilder (all three layers merged)
  → Jaccard deduplication
  → Keyword-overlap relevance ranking
  → tiktoken-accurate compression to budget
  → Injected as context for every LLM call
```

---

## Personas

ARIA's personality engine is stateless — switching personas never touches stored memory.

| Persona | Tone |
|---|---|
| `Assistant` | Warm, clear, helpful (default) |
| `Technical` | Precise, structured, analytical |
| `Creative` | Imaginative, narrative, fluid |
| `Socratic` | Questioning, philosophical, probing |

Switch via CLI: `/persona Technical`

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | API key (Groq or OpenAI-compatible) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Endpoint — set to Groq for free inference |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model (used only with OpenAI) |
| `OBSIDIAN_VAULT_PATH` | `C:\ARIA\ARIA-Memory-Vault` | Path to your Obsidian vault |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `TOP_K_VECTOR` | `3` | Number of vector results to retrieve |
| `MAX_CONTEXT_TOKENS` | `2000` | Hard token budget for injected context |
| `DATA_DIR` | `./data` | Directory for documents to index |
| `WATCH_DIRS` | — | Comma-separated dirs for auto-indexing |

---

## Showcased At

**National Louis University — AI Senior Capstone Showcase**  
May 8, 2026 | Chicago, IL  
**Result: 1st Place**

> *"Every AI tool you've used so far will do your homework for you. I built one that won't — and I want to show you why that's harder, and why it matters."*

Full presentation script and judge Q&A: [`docs/ARIA-Presentation-Guide.md`](docs/ARIA-Presentation-Guide.md)

---

## Author

**Vrajkumar Patel**  
BS Computer Science & Information Systems, AI Concentration  
National Louis University — Graduating Summer 2026  
F-1 Student | Open to AI/ML Engineering roles

[GitHub](https://github.com/vrajkumarpatel) · [Email](mailto:vp431030@gmail.com)

---

## License

MIT — see [LICENSE](LICENSE) for details.

PersonaEngine (the avatar/voice engine) is a separate open-source project by [@fagenorn](https://github.com/fagenorn/handcrafted-persona-engine). This repository contains only the Python memory backend and integration layer built by Vrajkumar Patel.
