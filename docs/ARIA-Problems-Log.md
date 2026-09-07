# ARIA Project — Problems & Resolutions Log

**Project:** PersonaEngine 3.0.2 — ARIA VTuber AI Companion  
**Showcase Deadline:** May 8, 2026 (NLU Capstone)  
**Stack:** Live2D · Qwen3 TTS (GGUF/ONNX) · ElevenLabs TTS · Audio2Face Lip Sync · Groq LLM · Neo4j Memory · Python Proxy

> **Scope note:** This is a raw debugging log kept during development and spans both sides of the project. Sections 1, 2, and 4 concern the third-party `PersonaEngine` avatar/TTS/lip-sync engine ([fagenorn/handcrafted-persona-engine](https://github.com/fagenorn/handcrafted-persona-engine)) — environment tuning and configuration, not original code. Section 3 (`llm_proxy.py`) is this repository's own Python code. See the top-level [README](../README.md#engineering-challenges) for the curated, correctly-attributed version of these entries.

---

## 1. CUDA / GPU Issues

### 1.1 — Qwen3 TTS: CUDA SM_120a Not Supported
**Symptom:** Qwen3 TTS failed to load on the RTX 5000-series (Blackwell) GPU.  
**Root Cause:** The bundled `ggml-cuda.dll` was compiled for older CUDA architectures and did not include SM_120a (native Blackwell).  
**Fix:** Replaced `ggml-cuda.dll` with a version compiled against CUDA 12.8 with native Blackwell support.

### 1.2 — Audio2Face: 30-Second ONNX Stalls with cuDNN 9.6
**Symptom:** LipSync pipeline stalled for ~30 seconds on each inference call after upgrading cuDNN.  
**Root Cause:** cuDNN 9.6 introduced a regression with the Audio2Face ONNX session initialization on this GPU.  
**Fix:** Reverted cuDNN to 9.1.1. `UseGpu=true` remains active.

### 1.3 — Qwen3 TTS vs Ollama GPU Contention
**Symptom:** System became unstable / crashed when both Qwen3 TTS and Ollama were running.  
**Root Cause:** Both processes fight for VRAM on the same GPU.  
**Fix:** Ollama removed from the stack. LLM moved fully to Groq API (cloud). Local GPU used exclusively for Qwen3 TTS + Audio2Face.

---

## 2. Qwen3 TTS — Voice / Audio Issues

### 2.1 — Word-by-Word Audio Stall (CTC Alignment Gating)
**Symptom:** ARIA's speech was delivered one word at a time with long pauses between words.  
**Root Cause:** The original synthesis session gated audio output on CTC forced-alignment results — audio was held back until each word's timestamp was confirmed.  
**Fix:** Rewrote `Qwen3SynthesisSession.cs` with a CTC bypass — audio chunks stream directly from `GenerateStreaming` without alignment gating. First chunk carries all phoneme tokens; subsequent chunks carry empty tokens. Subtitles still update; audio flows continuously.

### 2.2 — Stuttering (High Temperature + No Repetition Penalty)
**Symptom:** Audio had frequent stutters and spectral glitches throughout speech.  
**Root Cause:** `appsettings.json` had `Temperature: 1` (too high — causes chaotic codec frame selection) and `RepetitionPenalty: 1` (no penalty — allows identical frames to repeat, producing a stutter loop).  
**Fix:** `Temperature 1 → 0.6`, `RepetitionPenalty 1 → 1.05`.

### 2.3 — Residual Stuttering (Random Codec Groups + Small Chunks)
**Symptom:** Stutter reduced but still audible, especially on longer responses.  
**Root Cause:**  
- `CodePredictorGreedy: false` — codec groups 1–15 were sampled with randomness, causing spectral inconsistencies between frames.  
- `EmitEveryFrames: 8` — chunks were only 640ms; the bounded audio channel (size 2) gave the player a ~1.28s buffer. Occasional ONNX decode latency spikes caused buffer starvation → brief gaps.  
**Fix:** `CodePredictorGreedy: true`, `EmitEveryFrames 8 → 16` (1.28s chunks, ~2.56s buffer).

---

## 3. LLM Proxy (llm_proxy.py) Issues

### 3.1 — Proxy Not Running → "LLM Not Reachable"
**Symptom:** PersonaEngine showed LLM as unreachable.  
**Root Cause:** `llm_proxy.py` was not running. PersonaEngine's `TextEndpoint` points to `http://localhost:7777/v1` — if the proxy is down, all LLM calls fail.  
**Fix:** Start `python llm_proxy.py` in a terminal and keep it running alongside PersonaEngine.

### 3.2 — `/v1/models` Passthrough ConnectError on Startup
**Symptom:** Two `httpx.ConnectError` / TLS errors printed on startup; PersonaEngine briefly showed LLM as unreachable.  
**Root Cause:** PersonaEngine calls `GET /v1/models` to validate the endpoint. The proxy's catch-all passthrough forwarded this to Groq, but the TLS handshake failed (transient network issue).  
**Fix:** Added a local `GET /v1/models` handler in the proxy that returns a static model list without contacting Groq. Startup validation now always succeeds.

### 3.3 — Memory Date Question: Wrong Context Injected
**Symptom:** When asked "what date is it today?", ARIA gave wrong or evasive answers.  
**Root Cause:**  
1. Vector search matched the word "today" semantically and retrieved an irrelevant note ("Refibe might arrive 30 mins late to class today").  
2. The proxy never injected the actual current date anywhere in the context.  
**Fix:** Added `datetime.now()` injection at the top of the system prompt on every request: `[Current date: Thursday, May 01, 2026]`. The injected memory header already instructs the LLM to ignore irrelevant context.

### 3.4 — HTML Garbage in Memory Injection
**Symptom:** "Hello Aria" triggered a memory injection containing `<button type="button" aria-haspopup="dialog"...` — raw HTML from an Obsidian web-clip note polluting ARIA's context.  
**Root Cause:** Obsidian notes created by web-clipper plugins contain raw HTML markup. The memory retriever returned these without filtering.  
**Fix:** Added `_HTML_TAG` regex strip (`<[^>]{1,200}>`) applied to memory blocks before injection.

### 3.5 — Groq 429 Rate Limit (Empty / Failed Responses)
**Symptom:** `[Proxy] Groq HTTP 429` — ARIA gave no reply; PersonaEngine logged "no chunks received."  
**Root Cause (multiple factors):**  
- `llama-3.3-70b-versatile` free tier: 100K tokens/day, 12K TPM — exhausted from heavy testing.  
- Large memory injections (up to 1300+ chars) + full conversation history (6 turns) + personality.txt pushed each request close to or over TPM.  
- Rapid back-to-back turns burst into the 30 RPM limit.  
**Fixes applied (in order):**  
1. `max_turns 6 → 4` — shorter history per request.  
2. Memory cap at 700 chars — keeps injection under ~175 tokens.  
3. Retry logic: up to 3 attempts with 3s / 6s / 9s waits on 429.  
4. Proper non-200 error handling in streaming path — returns clean SSE `[DONE]` instead of hanging.  
5. Switched model to `llama-3.1-8b-instant` — 500K tokens/day (5×), 20K TPM, faster responses.  
6. 2.1-second minimum gap between Groq calls (`_groq_throttle`) — hard cap at ~28 RPM.

---

## 4. TTS Engine Switching

### 4.1 — ElevenLabs vs Qwen3 Trade-off
**Summary:**  
- **ElevenLabs** (`eleven_v3`): Zero stutter, reliable, but sounds slightly artificial / lacks natural expression.  
- **Qwen3**: Natural human-like voice with real emotional expression (sighs, laughs, prosody variation), but required significant tuning to eliminate stutter.  
**Current state:** Switchable via `Config.Tts.ActiveEngine` in `appsettings.json` (`"qwen3"` or `"elevenlabs"`). ElevenLabs is the fallback for reliability; Qwen3 is preferred when tuning is stable.

### 4.2 — ElevenLabs Voice ID Changes
Voice IDs tested during tuning:
| VoiceId | Notes |
|---|---|
| `exsUS4vynmxd379XN4yO` | Original |
| `EST9Ui6982FZPSi7gCHi` | Second test |
| `B8gJV1IhpuegLxdpXFOE` | Current (as of May 1, 2026) |

---

## 5. Current Active Configuration (May 1, 2026)

| Setting | Value |
|---|---|
| TTS Engine | `elevenlabs` |
| ElevenLabs Voice | `B8gJV1IhpuegLxdpXFOE` |
| ElevenLabs Model | `eleven_v3` |
| LLM (Groq) | `llama-3.1-8b-instant` |
| LLM Endpoint | `http://localhost:7777/v1` (proxy) |
| Qwen3 Temperature | `0.6` |
| Qwen3 RepetitionPenalty | `1.05` |
| Qwen3 EmitEveryFrames | `16` |
| Qwen3 CodePredictorGreedy | `true` |
| LipSync | Audio2Face, James identity, BVLS solver, GPU |
| cuDNN | 9.1.1 (NOT 9.6) |
| Memory history | 4 turns max |
| Memory injection cap | 700 chars |

---

## 6. Known Remaining Issues

- **Qwen3 stutter** — reduced significantly but not fully eliminated. `SilencePenaltyEnabled: true` with `silentHardStop = 15` can abruptly cut generation during natural pauses in longer responses (jokes, stories). May be worth testing `SilencePenaltyEnabled: false` if stutter reappears.
- **Vector memory mock mode** — `[Vector] setup failed: No files found in data` on every startup. HuggingFace embeddings load but vector store has no indexed data. Only Obsidian (file-based) memory is active.
- **Google Calendar not configured** — `authenticate()` never run. Calendar context unavailable.
- **Groq daily token quota** — on `llama-3.1-8b-instant` free tier. Heavy testing days may still exhaust quota. Consider having a backup Groq API key ready for showcase day.
