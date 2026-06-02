#!/usr/bin/env python3
"""
ARIA — REST Memory Bridge
Serves memory context to PersonaEngine (C#) over HTTP.
Author: Vrajkumar Patel

Endpoints:
  GET  /health              — liveness check
  POST /api/context         — query relevant memory for a user input
  POST /api/store           — store a completed conversation turn
  GET  /api/stats           — memory statistics
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time

from agent_core import (
    VectorMemory,
    GraphMemory,
    ContextBuilder,
    config,
)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="ARIA Memory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons (initialised once at startup) ──────────────────────────────────

vector_mem = VectorMemory()
graph_mem  = GraphMemory()
builder    = ContextBuilder()

_stats = {"queries": 0, "stores": 0, "started_at": int(time.time())}

# ── Request / Response models ─────────────────────────────────────────────────

class ContextRequest(BaseModel):
    user_input: str
    top_k: Optional[int] = 3

class ContextResponse(BaseModel):
    combined_context: str
    summary: str
    sources: list[str]
    semantic_memory: str
    graph_memory: str

class StoreRequest(BaseModel):
    user_input: str
    response: str
    persona: Optional[str] = "Assistant"

class StoreResponse(BaseModel):
    stored: bool
    message: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "vector": "live" if vector_mem.is_available else "mock",
        "graph":  "live" if graph_mem.is_available  else "fallback",
        "uptime_s": int(time.time()) - _stats["started_at"],
    }


@app.post("/api/context", response_model=ContextResponse)
def get_context(req: ContextRequest):
    """
    Called by PersonaEngine BEFORE the LLM.
    Returns filtered, compressed memory context for the given user input.
    """
    _stats["queries"] += 1

    vector_results = vector_mem.query(req.user_input, top_k=req.top_k)
    graph_results  = graph_mem.get_related_nodes(req.user_input)

    ctx = builder.build(
        user_input=req.user_input,
        vector_results=vector_results,
        graph_results=graph_results,
    )

    return ContextResponse(
        combined_context=ctx["combined_context"],
        summary=ctx["summary"],
        sources=ctx["sources"],
        semantic_memory=ctx["semantic_memory"],
        graph_memory=ctx["graph_memory"],
    )


@app.post("/api/store", response_model=StoreResponse)
def store_turn(req: StoreRequest):
    """
    Called by PersonaEngine AFTER the LLM responds.
    Persists the turn to both vector and graph memory.
    """
    _stats["stores"] += 1

    text = f"User: {req.user_input}\nARIA: {req.response}"
    vector_mem.store(text, {"type": "conversation", "persona": req.persona})

    ok = graph_mem.store_interaction(
        user_input=req.user_input,
        response=req.response,
        context_used={"sources": ["PersonaEngine"]},
    )

    return StoreResponse(
        stored=ok,
        message="Stored to vector + graph" if ok else "Vector only (graph unavailable)",
    )


@app.get("/api/stats")
def stats():
    return {
        **_stats,
        "vector_available": vector_mem.is_available,
        "graph_available":  graph_mem.is_available,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting ARIA Memory API on http://localhost:8765")
    print("  POST /api/context  — query memory")
    print("  POST /api/store    — store turn")
    print("  GET  /health       — status")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")
