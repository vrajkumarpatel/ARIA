#!/usr/bin/env python3
"""
ARIA — WebSocket + REST Memory Bridge
Serves real-time Neo4j graph data to any connected client (ARIA, browser, etc.)
Author: Vrajkumar Patel

Ports:
  8765 — FastAPI REST  (memory context + store)
  8766 — WebSocket     (live graph updates)
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Set

import uvicorn
import websockets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from agent_core import VectorMemory, ObsidianMemory, ContextBuilder, config
from agent_core.memory_graph import GraphMemory

# ── Shared singletons ─────────────────────────────────────────────────────────

vector_mem   = VectorMemory()
graph_mem    = GraphMemory()
obsidian_mem = ObsidianMemory()
builder      = ContextBuilder()

_stats = {"queries": 0, "stores": 0, "started_at": int(time.time())}

# Connected WebSocket clients — receives push on every memory store
_ws_clients: Set = set()


# ── REST API (port 8765) ──────────────────────────────────────────────────────

app = FastAPI(title="ARIA Memory Bridge", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ContextRequest(BaseModel):
    user_input: str
    top_k: int = 3

class StoreRequest(BaseModel):
    user_input: str
    response: str
    persona: str = "ARIA"

class IndexFilesRequest(BaseModel):
    path: str
    recursive: bool = True


@app.get("/health")
def health():
    ob_stats = obsidian_mem.get_all_stats()
    return {
        "status":    "ok",
        "vector":    "live" if vector_mem.is_available else "mock",
        "graph":     "live" if graph_mem.is_available  else "fallback",
        "obsidian":  f"{ob_stats['conversation_notes']} notes / {ob_stats['topic_nodes']} topics",
        "ws_clients": len(_ws_clients),
        "uptime_s":  int(time.time()) - _stats["started_at"],
    }


@app.post("/api/context")
async def get_context(req: ContextRequest):
    _stats["queries"] += 1
    vr = vector_mem.query(req.user_input, top_k=req.top_k)
    gr = graph_mem.get_related_nodes(req.user_input)
    ob = obsidian_mem.get_related_notes(req.user_input)

    # Merge Obsidian results into graph results — schemas are compatible
    combined_graph = gr + ob

    ctx = builder.build(req.user_input, vr, combined_graph)

    sources = ctx["sources"]
    if ob:
        sources = list(set(sources + ["Obsidian"]))

    return {
        "combined_context": ctx["combined_context"],
        "summary":          ctx["summary"],
        "sources":          sources,
        "semantic_memory":  ctx["semantic_memory"],
        "graph_memory":     ctx["graph_memory"],
    }


@app.post("/api/store")
async def store_turn(req: StoreRequest):
    _stats["stores"] += 1
    text = f"User: {req.user_input}\nARIA: {req.response}"
    vector_mem.store(text, {"type": "conversation", "persona": req.persona})
    ok = graph_mem.store_interaction(req.user_input, req.response,
                                     {"sources": ["PersonaEngine"]})
    obsidian_mem.store_interaction(req.user_input, req.response)

    # Push graph snapshot to all connected WebSocket clients
    if _ws_clients:
        snapshot = _build_graph_snapshot()
        msg = json.dumps({"type": "graph_update", "data": snapshot})
        disconnected = set()
        for ws in _ws_clients:
            try:
                await ws.send(msg)
            except Exception:
                disconnected.add(ws)
        _ws_clients -= disconnected

    return {"stored": ok, "message": "Stored to vector + graph"}


@app.get("/api/stats")
def stats():
    ob_stats = obsidian_mem.get_all_stats()
    return {**_stats,
            "vector_available":       vector_mem.is_available,
            "graph_available":        graph_mem.is_available,
            "obsidian_notes":         ob_stats["conversation_notes"],
            "obsidian_topic_nodes":   ob_stats["topic_nodes"],
            "obsidian_vault":         ob_stats["vault"],
            "ws_clients":             len(_ws_clients)}


@app.post("/api/index-files")
async def index_files(req: IndexFilesRequest):
    """Index a file or directory into vector memory so ARIA can retrieve it as context."""
    result = vector_mem.index_path(req.path, recursive=req.recursive)
    return result


@app.get("/api/graph")
def get_graph():
    """REST endpoint to pull current graph snapshot."""
    return _build_graph_snapshot()


# ── Graph snapshot builder ────────────────────────────────────────────────────

def _build_graph_snapshot() -> dict:
    """Query Neo4j (or fallback) and return nodes + edges."""
    nodes, edges = [], []

    if graph_mem.is_available and graph_mem._driver:
        try:
            with graph_mem._driver.session(database=graph_mem._db) as s:
                # Recent interactions
                result = s.run("""
                    MATCH (u:UserInput)-[:GENERATED]->(r:Response)
                    RETURN u.id AS uid, u.text AS utext, u.timestamp AS uts,
                           r.id AS rid, r.text AS rtext
                    ORDER BY u.timestamp DESC LIMIT 30
                """)
                for row in result:
                    nodes.append({"id": row["uid"], "label": row["utext"][:40],
                                  "type": "UserInput", "timestamp": row["uts"]})
                    nodes.append({"id": row["rid"], "label": row["rtext"][:40],
                                  "type": "Response"})
                    edges.append({"source": row["uid"], "target": row["rid"],
                                  "type": "GENERATED"})

                # Entities
                ents = s.run("MATCH (e:Entity) RETURN e.name AS name, e.type AS type LIMIT 20")
                for e in ents:
                    nodes.append({"id": f"ent_{e['name']}", "label": e["name"],
                                  "type": e["type"] or "Entity"})
        except Exception as ex:
            nodes.append({"id": "err", "label": f"Graph error: {ex}", "type": "Error"})
    else:
        # Fallback: show in-memory interactions
        for i, item in enumerate(graph_mem._fallback[-20:]):
            uid = item["id"]
            rid = uid + "_r"
            nodes.append({"id": uid, "label": item["user_input"][:40], "type": "UserInput"})
            nodes.append({"id": rid, "label": item["response"][:40],   "type": "Response"})
            edges.append({"source": uid, "target": rid, "type": "GENERATED"})

    # Deduplicate nodes by id
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n["id"] not in seen:
            seen.add(n["id"])
            unique_nodes.append(n)

    return {
        "nodes": unique_nodes,
        "edges": edges,
        "total_nodes": len(unique_nodes),
        "total_edges": len(edges),
        "neo4j_live": graph_mem.is_available,
    }


# ── WebSocket server (port 8766) ──────────────────────────────────────────────

async def ws_handler(ws):
    _ws_clients.add(ws)
    print(f"  [WS] Client connected ({len(_ws_clients)} total)")

    # Send current graph immediately on connect
    try:
        await ws.send(json.dumps({
            "type": "graph_snapshot",
            "data": _build_graph_snapshot(),
        }))

        async for raw in ws:
            try:
                msg = json.loads(raw)
                cmd = msg.get("command")

                if cmd == "get_graph":
                    await ws.send(json.dumps({
                        "type": "graph_snapshot",
                        "data": _build_graph_snapshot(),
                    }))

                elif cmd == "ping":
                    await ws.send(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _ws_clients.discard(ws)
        print(f"  [WS] Client disconnected ({len(_ws_clients)} remaining)")


async def start_ws_server():
    print("  WebSocket server on ws://localhost:8766")
    async with websockets.serve(ws_handler, "0.0.0.0", 8766):
        await asyncio.Future()


# ── Watchdog file auto-indexer ────────────────────────────────────────────────

_SUPPORTED_EXTS = {".txt", ".md", ".pdf", ".docx"}

class _AutoIndexHandler(FileSystemEventHandler):
    """Re-indexes any supported file that is created or modified."""
    def __init__(self, vm: VectorMemory):
        self._vm = vm
        self._cooldown: dict = {}  # path → last-indexed timestamp

    def _should_index(self, path: str) -> bool:
        if Path(path).suffix.lower() not in _SUPPORTED_EXTS:
            return False
        now = time.time()
        if now - self._cooldown.get(path, 0) < 5:  # 5s debounce
            return False
        self._cooldown[path] = now
        return True

    def on_created(self, event):
        if not event.is_directory and self._should_index(event.src_path):
            print(f"  [Watch] New file: {event.src_path}")
            self._vm.index_path(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._should_index(event.src_path):
            print(f"  [Watch] Modified: {event.src_path}")
            self._vm.index_path(event.src_path)


def start_file_watchers():
    if not WATCHDOG_AVAILABLE or not config.WATCH_DIRS:
        return None
    observer = Observer()
    handler  = _AutoIndexHandler(vector_mem)
    for d in config.WATCH_DIRS:
        p = Path(d)
        if p.exists():
            observer.schedule(handler, str(p), recursive=True)
            print(f"  [Watch] Watching: {p}")
        else:
            print(f"  [Watch] Directory not found, skipping: {p}")
    observer.start()
    return observer  # run forever


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  ARIA Memory Bridge")
    print(f"  REST  → http://localhost:8765")
    print(f"  WS    → ws://localhost:8766")
    print(f"  Neo4j → {'LIVE (' + config.NEO4J_URI + ')' if graph_mem.is_available else 'fallback'}")
    print("=" * 56)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    start_file_watchers()

    # Index the Obsidian vault on every startup so ARIA always has full context
    vault = Path(config.OBSIDIAN_VAULT_PATH)
    if vault.exists() and vector_mem.is_available:
        print(f"  [Startup] Indexing vault: {vault}")
        result = vector_mem.index_path(str(vault), recursive=True)
        print(f"  [Startup] Vault indexed — {result['indexed']} docs, {result['skipped']} skipped")

    # Start WebSocket in background
    loop.create_task(start_ws_server())

    # Start FastAPI
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=8765,
                                    loop="asyncio", log_level="warning")
    server = uvicorn.Server(uvicorn_config)
    loop.run_until_complete(server.serve())
