from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ── The contract Dagestan must fulfill ───────────────────────────────────────
#
#  This is the only thing Amoeba agents know about memory.
#  Dagestan implements DagestanBackend. Swap backends without touching agents.
#
# ─────────────────────────────────────────────────────────────────────────────

class DagestanBackend(ABC):
    """
    The interface every Dagestan backend must implement.
    """
    pass 

# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class MemorySnapshot:
    agent_name: str
    timestamp: datetime
    context: dict
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemorySnapshot":
        return cls(
            agent_name=data["agent_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data["context"],
            tags=data.get("tags", []),
        )


@dataclass
class RecallResult:
    content: dict
    score: float          # 0.0 → 1.0, higher = more relevant
    source: str           # "temporal" | "embedding" | "graph"
    timestamp: Optional[datetime] = None

    def __repr__(self):
        return f"RecallResult(source={self.source}, score={self.score:.2f})"


class InMemoryBackend(DagestanBackend):
    """
    Fully functional in-memory backend.
    Agents work completely with this — no Dagestan needed for development.
    Replace with DagestanLiveBackend when Dagestan's API is finalized.
    """
    pass 

class DagestanAdapter:
    """
    The memory interface for every Amoeba agent.

    Three verbs:
        snapshot()  — write this moment to the temporal layer
        recall()    — semantic search across embedding + temporal layers
        graph()     — relational query against the world model

    Backed by InMemoryBackend by default.
    Pass a DagestanLiveBackend instance to go live.
    """

    def __init__(self, backend: Optional[DagestanBackend] = None):
        self._backend = backend or InMemoryBackend()

    # ── Write ─────────────────────────────────────────────────────────────────

    def snapshot(
        self,
        agent_name: str,
        context: dict,
        tags: list[str] = [],
    ) -> MemorySnapshot:
        snap = MemorySnapshot(
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc),
            context=context,
            tags=tags,
        )
        self._backend.write_snapshot(snap)
        return snap

    def remember(
        self,
        agent_name: str,
        text: str,
        metadata: dict = {},
    ) -> None:
        """Write a chunk to the embedding layer for semantic recall later."""
        if isinstance(self._backend, InMemoryBackend):
            self._backend.write_chunk(agent_name, text, metadata)
        # DagestanLiveBackend will have its own chunk write path

    def relate(
        self,
        entity_a: str,
        relation: str,
        entity_b: str,
    ) -> None:
        """Add an edge to the graph layer."""
        if isinstance(self._backend, InMemoryBackend):
            self._backend.add_relation(entity_a, relation, entity_b)

    # ── Read ──────────────────────────────────────────────────────────────────

    def recall(
        self,
        agent_name: str,
        query: str,
        top_k: int = 5,
    ) -> Optional[RecallResult]:
        """
        Semantic recall — checks embedding layer first, falls back to
        latest temporal snapshot. Returns the single most relevant result.
        """
        # 1. Try embedding layer
        chunks = self._backend.search_chunks(agent_name, query, top_k=top_k)
        if chunks:
            best = max(chunks, key=lambda c: c["score"])
            return RecallResult(
                content=best,
                score=best["score"],
                source="embedding",
            )

        # 2. Fall back to latest temporal snapshot
        if isinstance(self._backend, InMemoryBackend):
            latest = self._backend.get_latest_snapshot(agent_name)
            if latest:
                return RecallResult(
                    content=latest.context,
                    score=0.5,  
                    source="temporal",
                    timestamp=latest.timestamp,
                )

        return None

    def recall_history(
        self,
        agent_name: str,
        limit: int = 10,
        since: Optional[datetime] = None,
    ) -> list[MemorySnapshot]:
        """Return raw temporal snapshots for an agent — useful for replay."""
        if isinstance(self._backend, InMemoryBackend):
            return self._backend.get_snapshots(agent_name, since=since, limit=limit)
        return []

    def graph(
        self,
        query: str,
        params: dict = {},
    ) -> Any:
        """Relational query against the world model graph."""
        return self._backend.graph_query(query, params)

    def connect(self, dagestan_client: Any) -> None:
        """
        Hot-swap from InMemoryBackend to live Dagestan.
        Call once Dagestan's client is initialized.

        Usage:
            memory = DagestanAdapter()           # starts in-memory
            ...
            memory.connect(dagestan_client)      # goes live, no agent changes
        """
        self._backend = DagestanLiveBackend(dagestan_client)

    def is_live(self) -> bool:
        return isinstance(self._backend, DagestanLiveBackend)

    def __repr__(self):
        mode = "live" if self.is_live() else "in-memory"
        return f"DagestanAdapter(mode={mode}, backend={self._backend})"