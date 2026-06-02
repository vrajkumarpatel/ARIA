import hashlib
import time
from typing import List, Dict

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

from .config import config


class GraphMemory:
    """
    Relationship mesh memory via Neo4j.
    ─────────────────────────────────────────────────────────────
    Graph model:
        (:UserInput)-[:GENERATED]->(:Response)
        (:UserInput)-[:MENTIONS]->(:Entity)

    Falls back to an in-process list when Neo4j is unavailable.
    ─────────────────────────────────────────────────────────────
    """

    def __init__(self):
        self._driver = None
        self._db = "neo4j"
        self._available = False
        self._fallback: List[Dict] = []

        if NEO4J_AVAILABLE:
            self._connect()

    # ── Public API ────────────────────────────────────────────

    def store_interaction(
        self,
        user_input: str,
        response: str,
        context_used: Dict = None,
    ) -> bool:
        """Persist one conversation turn as connected nodes."""
        uid = hashlib.md5(f"{user_input}{time.time()}".encode()).hexdigest()[:12]
        ts  = int(time.time())

        if not self._available:
            self._fallback.append(
                {"id": uid, "user_input": user_input, "response": response,
                 "context": context_used or {}, "timestamp": ts}
            )
            return True

        try:
            with self._driver.session(database=self._db) as s:
                s.run(
                    """
                    CREATE (u:UserInput  {id: $uid, text: $utext, timestamp: $ts})
                    CREATE (r:Response   {id: $rid, text: $rtext, timestamp: $ts})
                    CREATE (u)-[:GENERATED]->(r)
                    """,
                    uid=uid, rid=uid + "_r",
                    utext=user_input[:1000],
                    rtext=response[:2000],
                    ts=ts,
                )
                if context_used and context_used.get("sources"):
                    s.run(
                        "MATCH (u:UserInput {id:$uid}) SET u.sources=$src",
                        uid=uid,
                        src=",".join(context_used["sources"]),
                    )
            return True
        except Exception as e:
            print(f"  [Graph] store error: {e}")
            return False

    def get_related_nodes(self, text: str, limit: int = 5) -> List[Dict]:
        """Return past interactions whose input shares keywords with *text*."""
        if not self._available:
            return self._fallback_search(text, limit)

        words = [w.lower() for w in text.split() if len(w) > 3]
        if not words:
            return []

        try:
            with self._driver.session(database=self._db) as s:
                result = s.run(
                    """
                    MATCH (u:UserInput)-[:GENERATED]->(r:Response)
                    WHERE any(w IN $words WHERE toLower(u.text) CONTAINS w)
                    RETURN u.text AS user_input, r.text AS response,
                           u.timestamp AS ts
                    ORDER BY u.timestamp DESC
                    LIMIT $limit
                    """,
                    words=words[:6],
                    limit=limit,
                )
                return [
                    {
                        "user_input": row["user_input"],
                        "response":   row["response"],
                        "timestamp":  row["ts"],
                        "source":     "neo4j",
                    }
                    for row in result
                ]
        except Exception as e:
            print(f"  [Graph] query error: {e}")
            return []

    def add_entity(self, name: str, entity_type: str, properties: Dict = None):
        """Upsert a named entity node."""
        if not self._available:
            return
        try:
            with self._driver.session(database=self._db) as s:
                s.run(
                    "MERGE (e:Entity {name:$name}) SET e.type=$etype, e.updated=$ts",
                    name=name, etype=entity_type, ts=int(time.time()),
                )
        except Exception:
            pass

    def close(self):
        if self._driver:
            self._driver.close()

    @property
    def is_available(self) -> bool:
        return self._available

    # ── Internal ──────────────────────────────────────────────

    def _connect(self):
        try:
            self._driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
            )
            self._driver.verify_connectivity()
            self._available = True
            self._db = config.NEO4J_DATABASE
            self._ensure_schema()
            print(f"  [Graph] Connected to Neo4j: {config.NEO4J_URI}")
        except Exception as e:
            print(f"  [Graph] Neo4j unavailable: {e} — in-memory fallback active")

    def _ensure_schema(self):
        with self._driver.session(database=self._db) as s:
            s.run("CREATE INDEX ui_id IF NOT EXISTS FOR (n:UserInput) ON (n.id)")
            s.run("CREATE INDEX ent_name IF NOT EXISTS FOR (n:Entity)    ON (n.name)")

    def _fallback_search(self, text: str, limit: int) -> List[Dict]:
        words = set(text.lower().split())
        scored = [
            (len(words & set(item["user_input"].lower().split())), item)
            for item in self._fallback
        ]
        scored = [(s, i) for s, i in scored if s > 0]
        scored.sort(key=lambda x: (-x[0], -x[1]["timestamp"]))
        return [
            {"user_input": i["user_input"], "response": i["response"],
             "source": "fallback-graph"}
            for _, i in scored[:limit]
        ]
