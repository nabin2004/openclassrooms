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
    Minimal in-memory backend so Agent.think() works without Dagestan.
    Snapshots are retained for optional recall; embedding/graph paths are no-ops.
    """

    def __init__(self) -> None:
        self._snapshots: dict[str, list[MemorySnapshot]] = {}
        self._chunks: list[dict] = []

    def write_snapshot(self, snap: MemorySnapshot) -> None:
        self._snapshots.setdefault(snap.agent_name, []).append(snap)

    def search_chunks(
        self,
        agent_name: str,
        query: str,
        top_k: int = 5,
    ) -> list:
        return []

    def get_latest_snapshot(self, agent_name: str) -> Optional[MemorySnapshot]:
        seq = self._snapshots.get(agent_name, [])
        return seq[-1] if seq else None

    def get_snapshots(
        self,
        agent_name: str,
        since: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[MemorySnapshot]:
        seq = list(self._snapshots.get(agent_name, []))
        if since is not None:
            seq = [s for s in seq if s.timestamp >= since]
        return seq[-limit:]

    def write_chunk(
        self,
        agent_name: str,
        text: str,
        metadata: dict,
    ) -> None:
        self._chunks.append(
            {"agent_name": agent_name, "text": text, "metadata": metadata}
        )

    def add_relation(self, entity_a: str, relation: str, entity_b: str) -> None:
        pass

    def graph_query(self, query: str, params: dict) -> Any:
        return None


class DagestanLiveBackend(DagestanBackend):
    """Placeholder for a future Dagestan-backed implementation."""

    def __init__(self, client: Any):
        self._client = client


class StatelessMemoryAdapter:
    """
    No recall and no snapshot persistence. Use for one-shot agents where each
    call must not see prior turns or stored context.
    """

    def recall(
        self,
        agent_name: str,
        query: str,
        top_k: int = 5,
    ) -> None:
        return None

    def snapshot(
        self,
        agent_name: str,
        context: dict,
        tags: list[str] | None = None,
    ) -> None:
        return None


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