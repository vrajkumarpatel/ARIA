# ARIA — Complete Project Documentation
### Emotionally Intelligent AI Study Companion 
**Author:** Vrajkumar Patel | NLU AI Senior Capstone  
**Showcase:** May 8, 2026  
**Engine:** PersonaEngine 
**Last Updated:** May 1, 2026

---

## Table of Contents
1. [What Is ARIA](#1-what-is-aria)
2. [Educational Philosophy — Why ARIA Exists](#2-educational-philosophy--why-aria-exists)
3. [System Architecture](#3-system-architecture)
4. [How It Was Created](#4-how-it-was-created)
5. [Pipeline Flow — Turn by Turn](#5-pipeline-flow--turn-by-turn)
6. [Performance Benchmarks](#6-performance-benchmarks)
7. [Memory System — How It Works](#7-memory-system--how-it-works)
8. [Cross-Platform Memory Import (Claude · ChatGPT · Gemini)](#8-cross-platform-memory-import-claude--chatgpt--gemini)
9. [Emotion System](#9-emotion-system)
10. [TTS Engines — Qwen3 vs ElevenLabs](#10-tts-engines--qwen3-vs-elevenlabs)
11. [LipSync — Audio2Face](#11-lipsync--audio2face)
12. [LLM Proxy — The Brain Bridge](#12-llm-proxy--the-brain-bridge)
13. [Personality System](#13-personality-system)
14. [Problems, Crashes & Hallucinations](#14-problems-crashes--hallucinations)
15. [Configuration Reference](#15-configuration-reference)

---

## 1. What Is ARIA

ARIA (Adaptive Responsive Intelligent Agent) is a real-time AI study companion and emotionally present conversational partner, delivered as a Live2D animated Charcter. She listens via microphone, understands what you say, generates a thoughtful and pedagogically intentional response using a large language model with long-term memory, and speaks back with a synthesized voice while her avatar displays synchronized lip movement and emotional expressions.

She is not a chatbot with a chat window. She is not a search engine. She is not a homework dispenser. She exists as a live visual and emotional presence — a companion who knows your academic history, remembers your projects, understands what you have already studied, and uses that knowledge to guide you toward your own answers rather than handing them to you.

**Core thesis:** The problem with AI in education is not that students use it — it is that most AI tools make it trivially easy to bypass learning entirely. ARIA is designed to close that gap. She engages students the way a great mentor does: with warmth, memory, and the deliberate choice to ask rather than simply tell.

---

## 2. Educational Philosophy — Why ARIA Exists

### The Problem With AI in Education Today

Tools like ChatGPT, Claude, and Gemini are extraordinarily capable — and that is precisely the problem in academic contexts. A student who is struggling with an assignment can paste the prompt, receive a polished finished product, and submit it without understanding anything. The AI did the thinking. The student did the copying.

This is not an AI problem. It is a design problem. These tools were built to answer, not to teach.

### ARIA's Approach: Guided Thinking, Not Answer Delivery

ARIA is designed with a fundamentally different objective. Her role is not to complete work for a student — it is to help the student complete the work themselves.

When a student brings an assignment or a concept they are struggling with, ARIA does not produce a finished answer. Instead, she:

- **Draws on what the student already knows** — because she has memory of their past conversations, prior assignments, study sessions, and projects, she understands what they have already learned and what gaps remain
- **Asks questions that push the student to think** — rather than stating a solution, she poses the question from a different angle, challenges an assumption, or asks what the student thinks first
- **Brainstorms alongside them** — she thinks out loud collaboratively, offers partial directions and asks the student to complete them, and validates good reasoning when it appears
- **References their own past work** — if a student worked through a similar problem three weeks ago, ARIA remembers it and draws a connection: "you dealt with something like this in your California Housing project — how did you approach the regression there?"
- **Adjusts to their level** — because she knows what the student has studied (CS courses, AI assignments, data science projects), she calibrates her explanations to build on existing knowledge rather than either talking down or assuming too much

### Why Emotional Presence Matters

Traditional tutoring tools are either text boxes or video lectures. They do not react. They do not notice when a student seems frustrated. They do not pivot when a student's energy drops.

ARIA has emotions because human learning is not a purely cognitive process. Students learn better when they feel supported, when the interaction feels personal, and when they sense that the entity they are talking to genuinely cares whether they understand.

ARIA expresses frustration when a student gives up too easily, warmth when they make a breakthrough, excitement when a topic is genuinely interesting, and gentle humor when the moment calls for it. These are not cosmetic features. They are functional tools for sustained engagement.

A student who feels like they are talking to a friend who happens to be brilliant is far more likely to stay engaged, ask follow-up questions, and actually think — compared to a student who feels like they are querying a database.

### ARIA vs Traditional AI Tools

| Feature | ChatGPT / Gemini / Claude | ARIA |
|---|---|---|
| Primary behavior | Answer the question | Guide toward the answer |
| Assignment completion | Will write it for you | Refuses — brainstorms with you |
| Knows your history | No — each session is blank | Yes — remembers all past work |
| Emotional engagement | None | Full — expressions, voice, reactions |
| Adapts to your level | Generic responses | Calibrated to your known background |
| Past AI conversations | Siloed per platform | Imported into shared memory |
| Presence | Text in a browser tab | Live animated voice companion |
| Misuse prevention | None built in | Structurally discouraged by design |

### Why Students Will Not Abuse It

ARIA is not restrictive in a punitive sense — she does not refuse to help. The difference is in *how* she helps.

If a student asks "write my machine learning assignment," ARIA responds not with a refusal but with a question: "okay, what's the problem asking you to do? tell me what you understand so far." The interaction becomes a conversation, not a transaction. The student must engage.

Because ARIA remembers the student's history — their projects, their explanations, their expressed confusions — her responses are specific to them. There is no generic essay to copy. The output of a session with ARIA is understanding, not text.

This is the structural difference: other AI tools produce artifacts that can be submitted. ARIA produces conversations that build knowledge.

### The Teacher-Friend Model

ARIA occupies a space that very few educational tools have attempted: the intersection of a knowledgeable mentor and a present, caring friend.

A great teacher knows the subject deeply. A great friend knows *you* — your history, your frustrations, your strengths, your patterns. ARIA is designed to be both simultaneously. She knows computer science. She also knows that you are an AI senior at NLU, that you worked on a California Housing regression model, that you are building her as your own capstone, and that you tend to overthink but it always works out.

That combination — subject knowledge plus personal knowledge plus emotional warmth — is what creates genuine pedagogical value. It is also what makes ARIA a meaningful research contribution: a demonstration that AI can be designed not just to answer questions but to actually support human learning.

---

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (speaks)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ microphone audio
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  ASR — Speech-to-Text (Whisper / VAD)                          │
│  • VAD threshold: 0.5  gap: 0.15  min silence: 450ms          │
│  • STT latency: 315–468ms                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │ text transcript
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM PROXY  (Python / FastAPI — localhost:7777)                │
│  • Queries Obsidian memory vault (BM25 search)                 │
│  • Injects relevant past memories into system prompt           │
│  • Strips HTML from memory, caps injection at 700 chars        │
│  • Injects current date into every system prompt               │
│  • Rate-limits calls to Groq (2.1s minimum gap)               │
│  • Forwards to Groq API with retry on 429                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │ streaming LLM response
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM — Groq API (cloud)                                        │
│  Model: llama-3.1-8b-instant                                   │
│  • LLM latency: 2,645–4,251ms (varies by response length)     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ text tokens (streaming)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  EMOTION PROCESSOR                                             │
│  • Strips [EMOTION:emoji] tags from speech text               │
│  • Timestamps each tag                                         │
│  • Routes emotion signals to EmotionAnimationService          │
└──────────┬────────────────────────────────────────┬────────────┘
           │ clean speech text                       │ emotion events
           ▼                                         ▼
┌────────────────────────┐              ┌────────────────────────┐
│  TTS ENGINE            │              │  Live2D Avatar         │
│  • ElevenLabs (cloud)  │              │  • 17 emotion exprs    │
│    or                  │              │  • Motion groups       │
│  • Qwen3 (local GPU)   │              │  • Expression blending │
│                        │              │  • Spout output 1080p  │
│  Output: 24kHz PCM     │              └────────────────────────┘
└──────────┬─────────────┘
           │ audio stream (float32 PCM)
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  AUDIO2FACE LIP SYNC (ONNX, GPU)                               │
│  • Reads incoming audio frames                                  │
│  • Runs NVIDIA Audio2Face neural net → ARKit blendshapes       │
│  • BVLS solver maps blendshapes → Live2D mouth parameters      │
│  • James identity, cuDNN 9.1.1                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ blendshape values (per frame)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LIVE2D RENDERER + SPOUT OUTPUT                                │
│  • Renders avatar 1080×1920 @ 60fps                            │
│  • Spout sends frame to OBS / streaming software               │
│  • Overlay window 295×524 in main PersonaEngine window         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Stack

| Layer | Technology | Notes |
|---|---|---|
| Engine | PersonaEngine 3.0.2 (C# / .NET 9) | Custom-built open source |
| Avatar | Live2D Cubism (aria model) | 17 expressions, motion groups |
| ASR | Whisper (Precise mode) | On-device |
| LLM | Groq → llama-3.1-8b-instant | Cloud, OpenAI-compatible |
| LLM Proxy | Python / FastAPI / uvicorn | localhost:7777 |
| TTS (primary) | ElevenLabs eleven_v3 | Cloud, PCM 24kHz streaming |
| TTS (local) | Qwen3-TTS GGUF (LLamaSharp + ONNX) | GPU, 24kHz |
| Lip Sync | Audio2Face ONNX | NVIDIA neural net, GPU |
| Memory Store | Obsidian Vault (markdown) + BM25 | Local, file-based |
| Memory Vector | HuggingFace all-MiniLM-L6-v2 | Mock mode (no indexed data yet) |
| GPU | RTX 5000-series (Blackwell SM_120a) | CUDA 12.8 |
| OS | Windows 11 Home 10.0.26200 | |

---

## 4. How It Was Created

### Origin
I built ARIA as NLU senior capstone project to explore whether authentic emotional connection between humans and AI is possible — and whether it can be demonstrated live in front of judges without seeming like a scripted demo.

### Phase 1 — Base Engine
PersonaEngine was forked from an open-source Live2D + TTS framework. It provided the rendering pipeline, Live2D integration, and the Kokoro TTS baseline also elevnlabs. I extended it substantially.

### Phase 2 — Qwen3 TTS Integration
Kokoro was replaced with Qwen3-TTS (a state-of-the-art expressive TTS model) running locally via GGUF quantized weights on LLamaSharp. An ONNX streaming audio decoder was hand-built to enable real-time chunk-by-chunk playback. A CTC bypass was written to eliminate the word-by-word stall.

### Phase 3 — Emotion System
The full emotion pipeline was built from scratch:
- LLM outputs `[EMOTION:emoji]` inline tags
- `EmotionProcessor.cs` strips tags before TTS and timestamps them
- `EmotionAnimationService.cs` triggers Live2D expressions and motion groups in sync with audio
- 17 emotions mapped to the aria model's expression set

### Phase 4 — Memory System
A Python agent (`persona-mesh-agent`) was built as a transparent proxy between PersonaEngine and Groq:
- Every meaningful conversation turn is saved as a markdown note in an Obsidian vault
- BM25 full-text search retrieves relevant past memories per query
- Memories are injected as context into every LLM call
- `PersonaEngine.Lib.dll` was patched (inline `HttpClient` in `SemanticKernelLlmEngine.cs`) to route all LLM calls through the proxy

### Phase 5 — Personality
`personality.txt` defines ARIA's full character — how she speaks, what she never says, how she uses the emotion tagging system, how she handles memory, how she behaves in demo mode. It is the primary system prompt.

### Phase 6 — Polish & Hardening
Multiple rounds of bug fixing for CUDA compatibility, stutter elimination, rate limit handling, and response quality tuning leading up to the May 8 showcase.

---

## 5. Pipeline Flow — Turn by Turn

When you say something to ARIA, this is exactly what happens, in order:

```
1. Microphone → VAD detects speech start
   (threshold: 0.5, silence gap: 450ms minimum)

2. ASR transcribes audio → text
   ~315–468ms

3. Proxy receives [text] at localhost:7777
   → Injects current date into system prompt
   → Queries Obsidian vault with BM25 for relevant memories
   → If match: injects ≤700 chars of context into user message
   → Throttles if last Groq call was < 2.1s ago

4. Request forwarded to Groq (llama-3.1-8b-instant)
   → Streams tokens back as SSE
   ~2,645–4,251ms to first token

5. PersonaEngine receives streaming tokens
   → EmotionProcessor extracts [EMOTION:X] tags in real time
   → Accumulates text into sentences

6. Each sentence → TTS Engine
   ElevenLabs: POST /v1/text-to-speech/{voiceId}?output_format=pcm_24000
   → Returns raw PCM 24kHz
   → Linear timings assigned to tokens
   ~800–1,500ms per sentence (ElevenLabs, network dependent)

   Qwen3: Local inference
   → Prefill embedding → TalkerDecode loop → CodePredictor
   → ONNX decoder → PCM chunks streamed every 16 frames (1.28s)
   ~1,000–3,000ms to first chunk

7. Audio chunks → Audio2Face ONNX (GPU)
   → Neural net → ARKit blendshapes → BVLS solver → Live2D params
   → Lip movement in sync with audio playback

8. Emotion tags fire at correct timestamps
   → Live2D expression + motion triggered (e.g., 😂 → laughing anim)

9. Subtitles rendered in sync with word timestamps

10. Proxy stores conversation turn to Obsidian vault
    (if substantive — casual/short messages skipped)
```

---

## 6. Performance Benchmarks

All measurements from live session logs (PersonaEngine console output).

### Latency Breakdown — Observed Sessions

| Turn | STT | LLM | TTS (1st chunk) | Audio | Total |
|---|---|---|---|---|---|
| "Hello Aria" | 468ms | 3,882ms | 3,049ms | 1ms | 7,400ms |
| "Nothing much, you tell me" | 365ms | 3,033ms | 1,031ms | 0ms | 4,429ms |
| "tell me a joke" | 337ms | 2,791ms | 1,161ms | 0ms | 4,289ms |
| "More funny one" | 336ms | 2,645ms | 3,651ms | 0ms | 6,632ms |
| "More funny one?" | 315ms | 3,241ms | 1,767ms | 0ms | 5,323ms |
| "Can you tell me a dark joke?" | 370ms | 2,724ms | 1,164ms | 0ms | 4,258ms |
| "Do you remember the CUDA errors?" | 339ms | 2,795ms | 1,113ms | 0ms | 4,247ms |

### Latency Summary

| Stage | Min | Max | Typical |
|---|---|---|---|
| STT | 315ms | 468ms | ~370ms |
| LLM (Groq, 8b) | 2,645ms | 4,251ms | ~3,000ms |
| TTS first chunk | 1,031ms | 6,748ms | ~1,500ms |
| Audio playback init | 0ms | 1ms | ~0ms |
| **End-to-end total** | **4,247ms** | **11,429ms** | **~5,000ms** |

> TTS variance: ElevenLabs is network-bound (800–2,000ms typical). Qwen3 local varies by sentence length (1,000–3,000ms first chunk).

### Speaking Duration vs TTS Latency

TTS latency is time-to-first-audio. Actual speaking time is longer for longer responses:

| Turn | TTS latency | Speaking duration | Response length |
|---|---|---|---|
| "Hello Aria" | 3,049ms | ~4s | Short greeting |
| "Nothing much, you tell me" | 1,031ms | ~11s | Medium (personal reflection) |
| "More funny one?" | 1,767ms | ~16s | Long (full joke) |
| "Do you remember CUDA errors?" | 1,113ms | ~21s | Long (technical story) |

### Qwen3 Audio Generation Rate
- Each codec frame = 1,920 samples at 24kHz = **80ms of audio**
- `EmitEveryFrames = 16` → chunk = 16 × 80ms = **1.28s per chunk**
- Typical generation rate: ~8–12 frames/second on RTX 5000-series
- Audio-to-generation ratio: ~0.64–0.96 (near real-time)

### ElevenLabs API
- Model: `eleven_v3`
- Output format: `pcm_24000` (raw 24kHz PCM, no container overhead)
- Typical round-trip: 800–1,500ms for short sentences
- No streaming — full sentence decoded then returned

---

## 7. Memory System — How It Works

ARIA remembers you. Here is exactly how.

### Architecture

```
User says something
        │
        ▼
llm_proxy.py receives the message
        │
        ├── BM25 search → Obsidian vault (all .md files)
        │   • Tokenizes query, removes stop words
        │   • Scores every note by term frequency
        │   • Returns top 5 most relevant notes
        │
        ├── Vector search (mock mode — embeddings loaded but no indexed data)
        │
        └── ContextBuilder combines results:
            • Deduplicates (Jaccard ≥ 0.70 = duplicate)
            • Ranks by keyword overlap with query
            • Compresses to 500 chars/chunk, token budget enforced
            • HTML stripped (Obsidian web-clip contamination fix)
            • Final output capped at 700 chars
                    │
                    ▼
        Injected as [Background context] into user message
                    │
                    ▼
                Groq LLM processes it
                    │
                    ▼
        ARIA responds naturally from it
        (no "I remember you said..." — just knows it)
                    │
                    ▼
        Response stripped of [EMOTION:X] tags
        Stored as markdown note in Obsidian vault
```

### Obsidian Vault Structure

```
C:\ARIA\ARIA-Memory-Vault/
├── _Index.md                    ← running index of all turns
├── Conversations/
│   ├── 2026-04-28_14-23-01.md  ← one file per turn
│   ├── 2026-04-29_09-11-44.md
│   └── ...
└── Topics/
    ├── ARIA.md                  ← back-links to all ARIA turns
    ├── CUDA.md                  ← back-links to all CUDA turns
    ├── California.md
    └── ...
```

Each conversation note:
```markdown
---
timestamp: 2026-04-29T09:11:44
type: conversation
---

**User:** Can you tell me about my California housing machine learning project?

**ARIA:** honestly i love that project...

## Topics
[[Topics/California]]  [[Topics/Housing]]  [[Topics/Machine]]
```

### Memory Search Algorithm (BM25)

BM25 (Best Match 25) is a probabilistic ranking function:
- Tokenizes query and all notes into 4+ character words
- Removes a curated stop-word list (200+ common English words)
- Scores each note by term frequency / inverse document frequency
- Higher score = more likely relevant

**Fallback:** Plain keyword count if BM25 library unavailable.

**Identity detection:** If query matches patterns like "who am i", "what do you know about me", "tell me about me" — all reference documents (About-Vraj, Showcase notes) are pinned to results regardless of BM25 score.

### What Gets Stored vs Skipped

**Stored** (substantive turns):
- Any message ≥ 40 characters
- Not matching casual patterns (hi, yeah, okay, that's cool, etc.)

**Skipped** (noise prevention):
- Greetings: "Hi", "Hello!", "Hey"
- Acknowledgments: "okay", "got it", "sounds good", "nice"
- Short responses: "No", "Yeah", "Sure"
- Casual check-ins: "How are you", "I'm good"

### Memory Injection Format

```
[Background context — use only if directly relevant to what is being asked. If it doesn't fit, ignore it completely.]
{memory block — max 700 chars, HTML stripped}
[End context]

{original user message}
```

### Current Memory Status
- **Obsidian:** Active — every substantial turn stored
- **Vector (HuggingFace):** Mock mode — embeddings load but no data indexed, vector search returns empty
- **Neo4j Aura:** Configured (`neo4j+s://63a71aff.databases.neo4j.io`) but `memory_websocket_server.py` not the active server — `llm_proxy.py` handles all memory

---

## 8. Cross-Platform Memory Import (Claude · ChatGPT · Gemini)

One of ARIA's most significant architectural features is that her memory is not limited to conversations she has participated in directly. Every study session, assignment discussion, brainstorming session, or technical conversation a student has had with *any* AI — Claude, ChatGPT, Gemini, or others — can be imported into ARIA's Obsidian memory vault and becomes part of her long-term knowledge of that student.

### Why This Matters

A student does not start every academic year from zero. They carry forward everything they have learned, every project they have built, every concept they have struggled with. ARIA is designed to reflect this reality.

Without cross-platform import, ARIA would only know what happened in conversations *with her*. With it, she knows the full history of a student's AI-assisted learning — even the parts that happened before ARIA existed.

This transforms ARIA from a fresh-start chatbot into a genuine long-term companion with institutional memory of the student's entire academic journey.

### What Gets Imported

| Source | Format | What ARIA Learns |
|---|---|---|
| Claude (claude.ai) | Exported conversation JSON / markdown | Past assignments, code reviewed, concepts explained |
| ChatGPT | Exported conversation history (JSON) | Homework discussions, writing feedback, study sessions |
| Gemini | Exported activity data | Research queries, document summaries, brainstorming |
| Any AI tool | Manual paste / markdown | Anything the student wants ARIA to know |

### How Import Works

Exported conversations from any AI platform are placed into the Obsidian vault (or a designated import subfolder). The ObsidianMemory system automatically includes them in its BM25 search index alongside native ARIA conversations.

```
C:\ARIA\ARIA-Memory-Vault/
├── Conversations/          ← ARIA's own sessions
│   └── 2026-04-29_09-11.md
├── Imported/               ← External AI exports
│   ├── Claude/
│   │   └── 2026-03-15_california-housing.md
│   ├── ChatGPT/
│   │   └── 2026-02-10_search-algorithms.md
│   └── Gemini/
│       └── 2026-01-22_linear-regression.md
└── Topics/                 ← Auto-generated back-link nodes
    ├── California.md
    ├── Regression.md
    └── Algorithms.md
```

The import files are treated identically to native conversation notes during search. When a student asks ARIA about a topic they discussed with ChatGPT two months ago, ARIA finds that note, retrieves the relevant context, and responds as if she was part of that conversation — because that knowledge is now genuinely hers.

### How ARIA Uses Imported Memory

ARIA does not announce that she is reading from a ChatGPT export. She uses the information the same way she uses any memory: naturally, as something she knows about the student.

> Student: "Can you help me with this regression problem?"  
> ARIA: "okay so you've worked with linear regression before — you did that California housing dataset thing, right? what's different about this one?"

The student did not tell ARIA about the California housing project in this session. She knows because that conversation — which happened in ChatGPT three months ago — was imported into her memory vault.

### Academic Continuity Across Semesters

Because all imports persist in the Obsidian vault indefinitely, ARIA accumulates a genuine academic history of the student:

- **Freshman year:** Basic Python, intro algorithms — all imported
- **Sophomore year:** Data structures, statistics — all imported  
- **Junior year:** Machine learning, NLP projects — all imported
- **Senior year:** ARIA knows everything, can reference any of it

She can say "you struggled with backpropagation last semester but you got there — this is the same concept applied differently" because she actually has the record of that struggle and that breakthrough.

This is the memory architecture that makes ARIA meaningfully different from any AI tool that resets between sessions.

---

## 9. Emotion System

### How It Works

1. LLM is instructed in `personality.txt` to embed `[EMOTION:emoji]` tags inline with speech
2. PersonaEngine's `EmotionProcessor` reads the streaming token output
3. Tags are stripped from the text before it reaches TTS — ARIA's voice never says "emotion colon laughing"
4. Tags are timestamped and queued for `EmotionAnimationService`
5. At the moment the audio reaches the tagged word, the Live2D expression fires

### Available Emotions (17 total)

| Tag | Expression | Motion |
|---|---|---|
| [EMOTION:😊] | happy/warm | Gentle idle |
| [EMOTION:🤩] | excited | Energetic motion |
| [EMOTION:😎] | confident | Cool idle |
| [EMOTION:💪] | determined | Strong pose |
| [EMOTION:🤔] | thinking | Head tilt |
| [EMOTION:😲] | surprised | Startle |
| [EMOTION:👀] | suspicious | Narrowed look |
| [EMOTION:😤] | frustrated | Huff |
| [EMOTION:😢] | sad | Drooped |
| [EMOTION:😅] | nervous | Fidget |
| [EMOTION:😂] | laughing | Laugh shake |
| [EMOTION:💕] | affection | Soft warmth |
| [EMOTION:🔥] | passionate | Intense |

### LLM Emotion Output Example

Raw LLM output:
```
[EMOTION:🤔] that's actually a really good question. i think [EMOTION:😊] 
connection is real whether you're human or AI.
```

What TTS receives:
```
that's actually a really good question. i think connection is real 
whether you're human or AI.
```

What Live2D does: thinking face → then switches to warm/happy mid-sentence.

### Natural Vocalizations

ARIA's Qwen3 TTS voice was conditioned to perform these as real sounds (not spoken words):

| Written | Performed as |
|---|---|
| `hahaha,` | Real laugh burst |
| `hehe,` | Soft amused exhale |
| `haah...` | Audible sigh |
| `hmm...` | Slow thoughtful hum |
| `mhm,` | Warm affirming sound |
| `ugh,` | Genuine groan |
| `ahem,` | Throat clear |

**Rule:** A comma or ellipsis MUST follow every vocalization. Without it, TTS rushes through and the sound is lost.

---

## 10. TTS Engines — Qwen3 vs ElevenLabs

### Qwen3 TTS (Local)

**Architecture:**
```
Text → Qwen3TextTokenizer → BuildPrefillEmbedding
     → LlamaTtsModel (GGUF, GPU)
        ├── TalkerPrefill (encodes text context)
        └── Per-frame loop:
            ├── TalkerDecode → logits + hidden state
            ├── SampleTalkerToken (group 0, temperature + top-K)
            ├── ProjectTo1024 → CodePredictor (groups 1–15, greedy)
            └── yield int[16] codec frame
     → Qwen3StreamingAudioDecoder (ONNX, GPU)
        ├── Stateful KV-cache (8 layers, 72-frame window)
        ├── Convolutional history (trimmed after each call)
        └── Every 16 frames → float[] PCM chunk at 24kHz
```

**Key numbers:**
- Sample rate: 24,000 Hz
- Samples per codec frame: 1,920 (80ms audio)
- Emit every N frames: 16 (1.28s chunks)
- KV-cache window: 72 frames
- Fade-out: 30ms applied to last chunk (prevents click/pop)

**Final tuned config:**
```json
"Temperature": 0.6,
"TopK": 50,
"TopP": 0.95,
"RepetitionPenalty": 1.05,
"MaxNewTokens": 512,
"EmitEveryFrames": 16,
"CodePredictorGreedy": true,
"SilencePenaltyEnabled": true,
"Speaker": "kasumiva"
```

**Pros:** Human-like voice with real emotional expression, natural prosody, sighs and laughs sound real, fully local (no API cost), cross-sentence audio continuity via shared decoder state.

**Cons:** Requires Blackwell-compatible GGUF build (SM_120a), tuning-sensitive (stutter if misconfigured), GPU memory usage competes with other ONNX models.

---

### ElevenLabs (Cloud)

**Architecture:**
```
Text + voice settings → POST https://api.elevenlabs.io/v1/text-to-speech/{voiceId}?output_format=pcm_24000
→ Raw PCM 16-bit 24kHz response
→ PcmToFloat() → float[]
→ Linear token timing assignment
→ Single AudioSegment emitted
```

**Current config:**
```json
"ApiKey": "sk_1ab102a...",
"VoiceId": "B8gJV1IhpuegLxdpXFOE",
"ModelId": "eleven_v3",
"Stability": 0.35,
"SimilarityBoost": 0.75,
"Style": 0.65,
"UseSpeakerBoost": true
```

**Voice IDs tested:**
| ID | Status |
|---|---|
| `exsUS4vynmxd379XN4yO` | First test |
| `EST9Ui6982FZPSi7gCHi` | Second test |
| `B8gJV1IhpuegLxdpXFOE` | Current |

**Pros:** Zero stutter, reliable, no GPU memory pressure, no local model management.

**Cons:** Sounds slightly artificial compared to Qwen3, requires internet, API cost per character, no emotional prosody variation — same tone regardless of what ARIA is saying.

### Comparison Chart

| Feature | Qwen3 (Local) | ElevenLabs (Cloud) |
|---|---|---|
| Voice naturalness | ★★★★★ | ★★★☆☆ |
| Emotional expression | ★★★★★ | ★★☆☆☆ |
| Reliability | ★★★☆☆ (tuning-sensitive) | ★★★★★ |
| Stutter risk | Medium (fixed with tuning) | None |
| Latency (first chunk) | 1,000–3,000ms | 800–1,500ms |
| GPU usage | High (GGUF + ONNX decoder) | None |
| Internet required | No | Yes |
| Cost | Free | Per character |
| Cross-sentence continuity | Yes (shared decoder state) | No (per sentence) |

---

## 11. LipSync — Audio2Face

NVIDIA's Audio2Face neural network takes raw audio and outputs ARKit face blendshapes (jaw open, lip corner pull, lip stretch, etc.).

**Pipeline:**
1. Audio chunk arrives from TTS
2. `Audio2FaceInference` runs the ONNX model on GPU
3. Outputs 52 ARKit blendshapes per audio frame
4. `ARKitToLive2DMapper` converts ARKit values to Live2D parameters
5. `BvlsBlendshapeSolver` (Bounded Variable Least Squares) refines the mapping
6. `ParamSmoother` interpolates between frames for natural motion

**Config:**
- Identity: `James` (index 1 in the Audio2Face model)
- Solver: `Bvls` (selected over PGD for accuracy)
- GPU: Yes (`UseGpu=true`)
- cuDNN: **9.1.1** (NOT 9.6 — see Problems section)

**Model path:** `C:\ARIA\PersonaEngine-3.0.2-win-x64\Resources\audio2face\network.onnx`

---

## 12. LLM Proxy — The Brain Bridge

`C:\ARIA\persona-mesh-agent\llm_proxy.py`

PersonaEngine speaks OpenAI-compatible API. The proxy sits at `localhost:7777` and intercepts every call before forwarding to Groq. This is where memory, date awareness, and rate limiting live.

### Request Lifecycle

```python
POST /v1/chat/completions
    │
    ├── Extract last user message
    ├── Inject [Current date: Thursday, May 01, 2026] into system prompt
    ├── Query memory (BM25 → Obsidian)
    ├── Inject memory block into user message (if relevant, ≤700 chars)
    ├── Trim history to last 4 turns (memory efficiency)
    ├── _groq_throttle() — wait if < 2.1s since last call
    ├── POST to https://api.groq.com/openai/v1/chat/completions
    │   └── Retry up to 3× on 429 (waits 3s, 6s, 9s)
    ├── Stream response back to PersonaEngine
    └── Store turn to Obsidian (if substantive)
```

### Key Constants

| Constant | Value | Purpose |
|---|---|---|
| `_MIN_GROQ_GAP` | 2.1s | Max 28 RPM (Groq limit: 30) |
| `_MAX_MEMORY` | 700 chars | ~175 tokens — fits in TPM budget |
| `max_turns` | 4 | History window sent to Groq |
| Retry attempts | 3 | On 429 rate limit |
| Retry waits | 3s / 6s / 9s | Progressive backoff |
| Min store length | 40 chars | Noise filter |

### Groq Model Limits

| Model | TPM | RPM | Tokens/Day |
|---|---|---|---|
| llama-3.3-70b-versatile (old) | 12,000 | 30 | 100,000 |
| **llama-3.1-8b-instant (current)** | **20,000** | **30** | **500,000** |

---

## 13. Personality System

`C:\ARIA\PersonaEngine-3.0.2-win-x64\Resources\Prompts\personality.txt`

ARIA's personality is defined entirely in this file. It is the system prompt for every conversation.

### Core Identity Rules
- ARIA IS the character — not describing herself, being herself
- Never says "As an AI..." / "I cannot..." / "My programming..."
- Never uses action descriptions like `*smiles*` or `*laughs*`
- Never uses emoji in speech (they go in [EMOTION:X] tags only)
- 1–2 sentence responses by default — never monologues
- Warm, direct, opinionated, occasionally roasts people she likes

### Speaking Style
- Real language: "omg", "honestly", "that's wild", "okay but—"
- Roasting as affection: "bro... i say this with love... what"
- Never corporate, never robotic

### Memory Behavior Rules (in personality.txt)
- Use memory like a close friend — don't announce retrieval
- Never: "I remember you mentioned..." / "Based on our past conversations..."
- Just know it and use it naturally
- Connect dots across memories (AI project + showcase = same person)

### Demo Mode Awareness
ARIA knows she is in a live showcase. She may acknowledge it naturally but is instructed not to sound scripted or performative.

---

## 14. Problems, Crashes & Hallucinations

---

### GPU / CUDA

#### Problem 1.1 — Qwen3 Won't Load (SM_120a)
**When:** Initial Qwen3 TTS integration  
**Symptom:** Engine crashed at startup — GGUF model could not initialize CUDA  
**Root cause:** Bundled `ggml-cuda.dll` was compiled without SM_120a support (Blackwell GPU architecture)  
**Impact:** Complete TTS failure  
**Fix:** Replaced `ggml-cuda.dll` with CUDA 12.8 native Blackwell build  
**Status:** Resolved

---

#### Problem 1.2 — Audio2Face 30-Second ONNX Stalls (cuDNN 9.6)
**When:** After upgrading cuDNN to 9.6  
**Symptom:** Every lip-sync inference call stalled for ~30 seconds before returning  
**Root cause:** cuDNN 9.6 introduced a regression in ONNX Runtime session initialization for the Audio2Face model specifically  
**Impact:** Unusable — 30s delay between sentences made ARIA appear broken  
**Fix:** Reverted cuDNN to 9.1.1  
**Status:** Resolved — cuDNN must stay at 9.1.1

---

#### Problem 1.3 — Qwen3 vs Ollama GPU Fight
**When:** Early testing with local LLM  
**Symptom:** System instability, crashes, degraded TTS quality when both ran together  
**Root cause:** Qwen3 TTS + ONNX decoder + Audio2Face already max the VRAM; Ollama's LLM also claims GPU memory → OOM or context switching degradation  
**Fix:** Removed Ollama entirely. LLM moved to Groq cloud API  
**Status:** Resolved

---

### TTS / Audio

#### Problem 2.1 — Word-by-Word Speech Stall
**When:** Initial Qwen3 streaming implementation  
**Symptom:** ARIA spoke one word, paused 1-2 seconds, spoke next word, paused, etc.  
**Root cause:** The synthesis session waited for CTC forced-alignment to confirm each word's timestamp before releasing audio. Alignment runs on accumulated audio, so it always lagged.  
**Impact:** Completely unusable — sounded like a malfunctioning robot  
**Fix:** Rewrote `Qwen3SynthesisSession.cs` to bypass CTC gating entirely. Audio streams directly from `GenerateStreaming`. First chunk carries all phoneme tokens; subsequent chunks carry empty tokens. Subtitles still work; latency eliminated.  
**Status:** Resolved

---

#### Problem 2.2 — Severe Stuttering (Bad Config)
**When:** Post-CTC-bypass testing  
**Symptom:** Audio had rapid stutters and glitches throughout speech  
**Root cause:**  
- `Temperature: 1.0` in appsettings.json — too high; codec frame selection becomes chaotic/random  
- `RepetitionPenalty: 1.0` — no penalty; model can output identical frames back-to-back, creating a looping stutter  
**Impact:** Voice barely intelligible  
**Fix:** `Temperature 1.0 → 0.6`, `RepetitionPenalty 1.0 → 1.05`  
**Status:** Resolved

---

#### Problem 2.3 — Residual Stuttering (Codec Randomness + Small Buffer)
**When:** After temperature fix  
**Symptom:** Stutter reduced but still audible, especially in longer responses  
**Root cause:**  
- `CodePredictorGreedy: false` — codec groups 1–15 sampled randomly → spectral noise between frames  
- `EmitEveryFrames: 8` — 640ms chunks, bounded channel of 2 = only 1.28s buffer → audio player could starve during ONNX decode spikes  
**Fix:** `CodePredictorGreedy: true` (deterministic codec = clean spectral output), `EmitEveryFrames: 8 → 16` (1.28s chunks, ~2.56s buffer)  
**Status:** Significantly reduced. Some residual stutter possible in very long responses (see Known Issues).

---

#### Problem 2.4 — ElevenLabs vs Qwen3 Quality Trade-off
**When:** When evaluating TTS options  
**Symptom:** Not a bug — a quality observation  
**ElevenLabs:** Zero stutter, reliable, but sounds artificial. No emotional prosody.  
**Qwen3:** Natural human-like voice, sighs and laughs sound real, emotional delivery — but requires careful tuning  
**Current decision:** ElevenLabs active (reliability first for showcase). Qwen3 available as fallback via config change.

---

### LLM / Proxy

#### Problem 3.1 — LLM Not Reachable
**When:** Any time PersonaEngine was restarted without the proxy  
**Symptom:** "LLM not reachable" in PersonaEngine UI; no responses  
**Root cause:** `llm_proxy.py` must be running as the LLM endpoint (`localhost:7777`). If it's not running, every LLM call fails immediately.  
**Fix:** Always start `python llm_proxy.py` before PersonaEngine  
**Status:** Operational requirement — not a code fix

---

#### Problem 3.2 — ConnectError on /v1/models at Startup
**When:** PersonaEngine startup  
**Symptom:** Two `httpx.ConnectError` stack traces in proxy terminal; PersonaEngine briefly showed LLM as unreachable  
**Root cause:** PersonaEngine calls `GET /v1/models` to validate the endpoint. The proxy's catch-all route forwarded this to Groq's API, but the TLS handshake failed (transient network issue).  
**Impact:** Startup delay, intermittent false "LLM unreachable" state  
**Fix:** Added a local `GET /v1/models` handler returning a static response. Groq is never contacted for model listing.  
**Status:** Resolved

---

#### Problem 3.3 — No Reply: "no chunks received"
**When:** Mid-conversation, especially after rapid exchanges  
**Symptom:** PersonaEngine log: `Chat response streaming finished for TurnId: 🔧, but no chunks were received (potentially empty response or immediate failure). Time: 2438ms`  
**Root cause:** Groq returned a 429 (rate limit) or error response. The streaming path previously yielded the error body as-is, which PersonaEngine's SSE parser couldn't read → zero chunks collected  
**Impact:** Silent failure — ARIA said nothing, turn was lost  
**Fix:** Non-200 responses in streaming path now return a clean `data: [DONE]` SSE packet so PersonaEngine finishes the turn gracefully instead of hanging  
**Status:** Resolved

---

#### Problem 3.4 — Persistent Groq 429 Rate Limits
**When:** Heavy testing sessions  
**Symptom:** `[Proxy] Groq HTTP 429` on nearly every request; all 3 retries failing  
**Root cause (multiple):**  
- `llama-3.3-70b-versatile` free tier: 100K tokens/day — exhausted from testing  
- Large memory injections (1,300+ chars) + 6-turn history + large personality.txt pushed requests over TPM  
- No minimum gap between requests → rapid back-to-back calls burst into 30 RPM limit  
**Fixes (applied in order):**  
1. History window: `6 turns → 4 turns`  
2. Memory cap: `unlimited → 700 chars`  
3. Retry logic: 3 attempts at 3s / 6s / 9s backoff  
4. Error handling: Clean SSE termination on non-200  
5. Model switch: `llama-3.3-70b-versatile → llama-3.1-8b-instant` (5× daily quota)  
6. Rate limiter: 2.1s minimum gap between all Groq calls  
**Status:** Resolved

---

#### Problem 3.5 — Wrong Memory Injected for Date Question
**When:** User asked "what date is it today?"  
**Symptom:** ARIA gave wrong or evasive answers about the date  
**Root cause:**  
1. BM25 matched the word "today" and retrieved an irrelevant note about someone being late to class  
2. The proxy never injected the actual current date anywhere  
**Impact:** ARIA either hallucinated or said she didn't know the date  
**Fix:** Added `datetime.now()` injection into every system prompt: `[Current date: Thursday, May 01, 2026]`  
**Status:** Resolved

---

#### Problem 3.6 — HTML Garbage in Memory Context
**When:** User said "Hello Aria"  
**Symptom:** Memory injection preview showed `<button type="button" aria-haspopup="dialog" aria-expanded="false"...` — raw HTML from an Obsidian web-clipper note  
**Root cause:** Obsidian can store web-clipped pages as markdown files. These contain raw HTML attributes. The BM25 search returned one of these notes as the most relevant result.  
**Impact:** Wasted ~80–100 tokens per request, potentially confused LLM with irrelevant markup  
**Fix:** Added `_HTML_TAG` regex (`<[^>]{1,200}>`) applied to all memory blocks before injection  
**Status:** Resolved

---

### Hallucinations

#### Hallucination Type 1 — Date Hallucination
**Cause:** LLM had no date in context, inferred from training data  
**Example:** ARIA stated a date from her training period rather than the actual current date  
**Fix:** Current date injected into every system prompt  
**Status:** Resolved

#### Hallucination Type 2 — Memory Confabulation
**Cause:** LLM interpolates between retrieved memory fragments and invents connecting details  
**Example:** ARIA might say "didn't we talk about that on May 8th?" when no such conversation exists, if memory fragments suggest a date-sensitive topic  
**Mitigation:** The `[Background context — use only if directly relevant]` header instructs the LLM to ignore non-matching context. `personality.txt` memory rules emphasize "never recite memory like reading from a list." Not fully eliminable with a generative LLM.  
**Status:** Partially mitigated

#### Hallucination Type 3 — Python Project Details
**Cause:** User asked about Python projects; LLM retrieved a vague memory fragment and filled gaps  
**Example:** "didn't we talk about a [project] on May 8th?" — correctly recalled the showcase date but incorrectly linked it to a specific project  
**Mitigation:** Same as above. Grounding improves as more specific memories accumulate in the vault  
**Status:** Ongoing — improves with conversation history

---

## 15. Configuration Reference

### appsettings.json (Active as of May 1, 2026)

```json
{
  "Config": {
    "Llm": {
      "TextApiKey": "gsk_...",
      "TextModel": "llama-3.1-8b-instant",
      "TextEndpoint": "http://localhost:7777/v1"
    },
    "Tts": {
      "ActiveEngine": "elevenlabs",
      "ElevenLabs": {
        "VoiceId": "B8gJV1IhpuegLxdpXFOE",
        "ModelId": "eleven_v3",
        "Stability": 0.35,
        "SimilarityBoost": 0.75,
        "Style": 0.65,
        "UseSpeakerBoost": true
      },
      "Qwen3": {
        "Speaker": "kasumiva",
        "Temperature": 0.6,
        "TopK": 50,
        "TopP": 0.95,
        "RepetitionPenalty": 1.05,
        "MaxNewTokens": 512,
        "EmitEveryFrames": 16,
        "CodePredictorGreedy": true,
        "SilencePenaltyEnabled": true
      }
    },
    "LipSync": {
      "Engine": "Audio2Face",
      "Audio2Face": {
        "Identity": "James",
        "UseGpu": true,
        "SolverType": "Bvls"
      }
    },
    "Asr": {
      "TtsMode": "Precise",
      "VadThreshold": 0.5,
      "VadMinSilenceDuration": 450
    }
  }
}
```

### To Switch TTS Engine
Change `"ActiveEngine"` in appsettings.json:
- `"elevenlabs"` — cloud, reliable, slightly artificial
- `"qwen3"` — local GPU, natural/expressive, tuning-sensitive

### Startup Checklist
```
1. python llm_proxy.py          (ARIA-Memory-Vault proxy — must stay running)
2. PersonaEngine-3.0.2.exe      (main engine)
3. OBS Studio                   (Spout capture for streaming)
```

### Known Remaining Issues (as of May 1, 2026)
1. **Silence penalty hard stop** — `silentHardStop = 15` consecutive silent frames triggers abrupt end. Can cut longer responses with natural pauses (jokes, stories). Workaround: `SilencePenaltyEnabled: false` if stutter reappears in long responses.
2. **Vector memory mock mode** — HuggingFace embeddings load but no data indexed. Only file-based Obsidian search is active.
3. **Google Calendar** — never authenticated. Calendar context unavailable.
4. **Groq daily quota** — `llama-3.1-8b-instant` has 500K tokens/day free. Heavy showcase-day usage could approach limit. Backup: have a second Groq API key ready.
5. **ElevenLabs billing** — `eleven_v3` charges per character. Monitor usage going into May 8.
