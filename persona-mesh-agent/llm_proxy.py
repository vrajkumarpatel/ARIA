#!/usr/bin/env python3
"""
ARIA — LLM Memory Proxy
Author: Vrajkumar Patel
========================
Sits between PersonaEngine (C#) and Groq API.
On every /v1/chat/completions call:
  1. Extracts the user's message
  2. Queries Neo4j for relevant past memories
  3. Injects memories into the system prompt
  4. Forwards to real Groq API
  5. Stores the turn to Neo4j
  6. Returns the response transparently

PersonaEngine config:
  TextEndpoint = http://localhost:7777/v1
  TextApiKey   = (anything — proxy uses its own key)
"""

import asyncio
import httpx
import json
import time
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from agent_core import ObsidianMemory, VectorMemory, ContextBuilder, config
from agent_core.calendar_fetcher import get_upcoming_events, format_for_context, is_configured as calendar_ready

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY  = config.OPENAI_API_KEY
GROQ_ENDPOINT = "https://api.groq.com/openai/v1"
PROXY_PORT    = 7777

# ── Memory singletons ─────────────────────────────────────────────────────────

obsidian   = ObsidianMemory()
vector_mem = VectorMemory()
builder    = ContextBuilder()

print(f"  Obsidian vault: {config.OBSIDIAN_VAULT_PATH}")
print(f"  Google Calendar: {'connected' if calendar_ready() else 'not configured — run authenticate() once'}")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="ARIA Memory Proxy", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_stats = {"requests": 0, "memory_injections": 0, "stores": 0}

# ── Rate limiter — enforces minimum gap between Groq calls ────────────────────
_groq_lock      = asyncio.Lock()
_last_groq_call = 0.0
_MIN_GROQ_GAP   = 2.1  # seconds — keeps us safely under 30 RPM

async def _groq_throttle():
    global _last_groq_call
    async with _groq_lock:
        now  = asyncio.get_event_loop().time()
        wait = _last_groq_call + _MIN_GROQ_GAP - now
        if wait > 0:
            await asyncio.sleep(wait)
        _last_groq_call = asyncio.get_event_loop().time()


# ── Helpers ───────────────────────────────────────────────────────────────────

import re as _re
_USER_PREFIX  = _re.compile(r"^\[User\]\s*", _re.IGNORECASE)
_EMOTION_TAG  = _re.compile(r"\[EMOTION:[^\]]*\]")
_HTML_TAG     = _re.compile(r"<[^>]{1,200}>")
_MAX_MEMORY   = 700  # chars — keeps memory injection under ~175 tokens

def _clean_user(text: str) -> str:
    """Strip [User] prefix PersonaEngine adds to message content."""
    return _USER_PREFIX.sub("", text).strip()

def _clean_response(text: str) -> str:
    """Strip [EMOTION:...] tags before storing so memory is clean text."""
    return _EMOTION_TAG.sub("", text).strip()

def _extract_last_user_message(messages: list) -> str | None:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return _clean_user(part["text"])
            return _clean_user(str(content))
    return None


def _trim_history(messages: list, max_turns: int = 4) -> list:
    """Keep system messages + last N user/assistant turn pairs to avoid context overflow."""
    system = [m for m in messages if m.get("role") == "system"]
    convo  = [m for m in messages if m.get("role") != "system"]
    # Keep last max_turns * 2 messages (each turn = 1 user + 1 assistant)
    trimmed = convo[-(max_turns * 2):]
    return system + trimmed


def _build_memory_block(user_input: str) -> str | None:
    """Return compressed memory + calendar context, or None if nothing relevant."""
    vr  = vector_mem.query(user_input, top_k=3) if vector_mem.is_available else []
    gr  = obsidian.get_related_notes(user_input, limit=5)
    ctx = builder.build(user_input, vr, gr)
    combined = ctx.get("combined_context", "")

    # Append upcoming calendar events
    if calendar_ready():
        events = get_upcoming_events(days=7)
        schedule = format_for_context(events)
        if schedule:
            combined = (combined.strip() + "\n\n" + schedule) if combined and combined != "No relevant memory found." else schedule

    if not combined or combined == "No relevant memory found." or len(combined) < 80:
        return None

    # Strip HTML that leaks in from Obsidian web-clip notes
    combined = _HTML_TAG.sub("", combined).strip()

    # Cap size to stay well under Groq's TPM limit
    if len(combined) > _MAX_MEMORY:
        combined = combined[:_MAX_MEMORY].rsplit(" ", 1)[0] + "…"

    if len(combined) < 80:
        return None
    return combined


def _inject_memory(messages: list, memory_block: str) -> list:
    """Prepend memory context directly into the last user message content."""
    patched = list(messages)
    for i in range(len(patched) - 1, -1, -1):
        if patched[i].get("role") == "user":
            original = patched[i].get("content", "")
            if isinstance(original, list):
                # multipart content — prepend to the first text part
                parts = list(original)
                for j, part in enumerate(parts):
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts[j] = {**part, "text": (
                            f"[Background context — use only if directly relevant to what is being asked. If it doesn't fit, ignore it completely.]\n"
                            f"{memory_block}\n"
                            f"[End context]\n\n"
                            f"{part['text']}"
                        )}
                        break
                patched[i] = {**patched[i], "content": parts}
            else:
                patched[i] = {**patched[i], "content": (
                    f"[Background context — use only if directly relevant to what is being asked. If it doesn't fit, ignore it completely.]\n"
                    f"{memory_block}\n"
                    f"[End context]\n\n"
                    f"{original}"
                )}
            return patched
    return patched


_CASUAL = _re.compile(
    r"^(hi+|hey+|hello+|bye|okay|ok|yes|no|yeah|sure|thanks|thank you|"
    r"how are you|i(\'?m| am) (good|fine|okay)|that(\'?s)? (cool|nice|great)|"
    r"got it|sounds good|i see|nice|great|cool|interesting|go on|continue|"
    r"really|wow|oh|hmm+|ugh|lol|haha|it(\'?s)? (done|finished|ready)|"
    r"(hi|hey|hello)[,\s]+(i(\'?m| am)|my name is)\s+\w+|"   # "Hi I'm the judge"
    r"i(\'?m| am) (the |a |an )?\w+)[\s\W]*$",               # "I'm the judge"
    _re.IGNORECASE,
)

def _should_store(user_input: str) -> bool:
    """Skip casual/trivial turns that add noise to memory."""
    text = user_input.strip()
    if len(text) < 40:          # raised from 20 — short messages are almost always noise
        return False
    if _CASUAL.match(text):
        return False
    return True

def _store_turn(user_input: str, assistant_reply: str):
    """Persist meaningful turns to Obsidian (+ vector if real embeddings live)."""
    if not _should_store(user_input):
        print(f"  [Memory] Skip store (casual): {user_input[:50]}")
        return
    clean_reply = _clean_response(assistant_reply)
    # Only use vector store when real embeddings are available — mock mode is noise
    if vector_mem.is_available:
        vector_mem.store(user_input, {"type": "conversation", "response": clean_reply})
    obsidian.store_interaction(user_input, clean_reply, {"sources": ["PersonaEngine"]})
    _stats["stores"] += 1
    print(f"  [Memory] Stored: {user_input[:60]}")


# ── Main proxy endpoint ───────────────────────────────────────────────────────

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    _stats["requests"] += 1
    body = await request.json()

    messages    = body.get("messages", [])
    is_stream   = body.get("stream", False)
    user_input  = _extract_last_user_message(messages)

    # 0. Inject current date into system prompt
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    date_note = f"[Current date: {today_str}]"
    messages = list(messages)
    for i, m in enumerate(messages):
        if m.get("role") == "system":
            messages[i] = {**m, "content": date_note + "\n" + m.get("content", "")}
            break

    # 1. Query memory
    patched_messages = messages
    if user_input:
        memory_block = _build_memory_block(user_input)
        if memory_block:
            patched_messages = _inject_memory(messages, memory_block)
            _stats["memory_injections"] += 1
            print(f"  [Memory] Injected ({len(memory_block)} chars) for: {user_input[:60]}")
            print(f"  [Memory] Preview: {memory_block[:120].replace(chr(10), ' ')}")
        else:
            print(f"  [Memory] No match for: {user_input[:60]}")

    # 2. Trim history to avoid context overflow, then forward to Groq
    patched_messages = _trim_history(patched_messages)
    body["messages"] = patched_messages
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    if is_stream:
        # ── Streaming path ────────────────────────────────────────────────────
        async def stream_and_store():
            collected_reply = []
            async with httpx.AsyncClient(timeout=60) as client:
                for attempt in range(3):
                    await _groq_throttle()
                    async with client.stream(
                        "POST", f"{GROQ_ENDPOINT}/chat/completions",
                        json=body, headers=headers
                    ) as resp:
                        if resp.status_code == 429:
                            error_body = await resp.aread()
                            wait = 3 * (attempt + 1)
                            print(f"  [Proxy] Groq 429 rate limit (attempt {attempt+1}/3) — retrying in {wait}s")
                            await asyncio.sleep(wait)
                            continue
                        if resp.status_code != 200:
                            error_body = await resp.aread()
                            print(f"  [Proxy] Groq HTTP {resp.status_code}: {error_body[:200]}")
                            err_json = json.dumps({
                                "id": "err", "object": "chat.completion.chunk",
                                "choices": [{"index": 0, "delta": {"content": ""}, "finish_reason": "stop"}]
                            })
                            yield f"data: {err_json}\n\ndata: [DONE]\n\n".encode()
                            return
                        async for chunk in resp.aiter_bytes():
                            yield chunk  # stream immediately — never buffer
                            for line in chunk.decode("utf-8", errors="ignore").splitlines():
                                if line.startswith("data: ") and line != "data: [DONE]":
                                    try:
                                        d = json.loads(line[6:])
                                        delta = d["choices"][0].get("delta", {})
                                        if delta.get("content"):
                                            collected_reply.append(delta["content"])
                                    except Exception:
                                        pass
                        break  # success — exit retry loop

            if user_input and collected_reply:
                _store_turn(user_input, "".join(collected_reply))
            elif not collected_reply:
                print(f"  [Proxy] No reply after retries for: {(user_input or '')[:60]}")

        return StreamingResponse(stream_and_store(),
                                 media_type="text/event-stream")

    else:
        # ── Non-streaming path ────────────────────────────────────────────────
        await _groq_throttle()
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{GROQ_ENDPOINT}/chat/completions",
                                     json=body, headers=headers)
        data = resp.json()

        # Store the turn
        if user_input:
            try:
                reply = data["choices"][0]["message"]["content"]
                _store_turn(user_input, reply)
            except Exception:
                pass

        return Response(content=resp.content,
                        status_code=resp.status_code,
                        media_type="application/json")


# ── Local models list (avoids TLS round-trip to Groq on startup) ─────────────

@app.get("/v1/models")
async def models():
    return {
        "object": "list",
        "data": [{"id": "meta-llama/llama-4-scout-17b-16e-instruct", "object": "model",
                  "created": 0, "owned_by": "groq"}]
    }


# ── Pass-through for other endpoints ─────────────────────────────────────────

@app.api_route("/v1/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def passthrough(path: str, request: Request):
    body = await request.body()
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  request.headers.get("content-type", "application/json"),
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(
            method=request.method,
            url=f"{GROQ_ENDPOINT}/{path}",
            content=body,
            headers=headers,
        )
    return Response(content=resp.content, status_code=resp.status_code,
                    media_type=resp.headers.get("content-type", "application/json"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "obsidian": str(config.OBSIDIAN_VAULT_PATH),
        "vector": "live" if vector_mem.is_available else "mock",
        **_stats,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  ARIA Memory Proxy")
    print(f"  Listening on  http://localhost:{PROXY_PORT}/v1")
    print(f"  Forwarding to {GROQ_ENDPOINT}")
    print("=" * 56)
    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT, log_level="warning")
