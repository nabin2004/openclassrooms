from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from amoeba.core.agent import Agent


# ── Tick record — what happened in one cognitive cycle ───────────────────────

class TickStatus(str, Enum):
    SUCCESS  = "success"
    FAILED   = "failed"
    SKIPPED  = "skipped"   # agent chose not to act this cycle


@dataclass
class TickRecord:
    tick_number: int
    agent_name: str
    status: TickStatus
    timestamp: datetime
    duration_ms: float
    input_summary: str = ""
    output_summary: str = ""
    tools_called: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def __repr__(self):
        return (
            f"TickRecord(#{self.tick_number} {self.agent_name} "
            f"{self.status.value} {self.duration_ms:.1f}ms)"
        )


# ── TickContext — what the agent receives each cycle ─────────────────────────

@dataclass
class TickContext:
    """
    Everything an agent needs to reason in one tick.
    Passed into agent.run(state) as the state dict.
    """
    tick_number: int
    timestamp: datetime
    state: dict                          # full pipeline state
    elapsed_since_last_ms: float = 0.0  # time since previous tick
    metadata: dict = field(default_factory=dict)

    def to_state(self) -> dict:
        """Merge tick metadata into state for agent.run()."""
        return {
            **self.state,
            "_tick": self.tick_number,
            "_timestamp": self.timestamp.isoformat(),
            "_elapsed_ms": self.elapsed_since_last_ms,
        }


# ── Ticker — wraps an agent and drives its cognitive loop ────────────────────

class Ticker:
    """
    Drives an agent's cognitive loop.

    Now:      call tick() manually — one cycle per call
    Later:    call run_at(hz=10) — continuous embodied loop

    Usage:
        ticker = Ticker(agent)

        # manual tick (LangGraph mode, Manimator now)
        record = await ticker.tick(state)

        # continuous loop (embodied mode, future)
        await ticker.run_at(hz=10, env=sim_env)
    """

    def __init__(self, agent: "Agent", max_history: int = 100):
        self.agent = agent
        self.max_history = max_history

        self._tick_count: int = 0
        self._history: list[TickRecord] = []
        self._last_tick_time: Optional[float] = None
        self._running: bool = False

    # ── Single tick ───────────────────────────────────────────────────────────

    async def tick(self, state: dict) -> TickRecord:
        """
        Execute one complete cognitive cycle.
        Returns a TickRecord describing what happened.
        """
        self._tick_count += 1
        now = time.perf_counter()
        elapsed = (
            (now - self._last_tick_time) * 1000
            if self._last_tick_time
            else 0.0
        )

        ctx = TickContext(
            tick_number=self._tick_count,
            timestamp=datetime.now(timezone.utc),
            state=state,
            elapsed_since_last_ms=elapsed,
        )

        start = time.perf_counter()
        try:
            result_state = await self.agent.run(ctx.to_state())
            duration_ms  = (time.perf_counter() - start) * 1000

            record = TickRecord(
                tick_number=self._tick_count,
                agent_name=self.agent.name,
                status=TickStatus.SUCCESS,
                timestamp=ctx.timestamp,
                duration_ms=duration_ms,
                input_summary=str(state.get("input", ""))[:120],
                output_summary=str(
                    result_state.get(f"{self.agent.name}_output", "")
                )[:120],
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            record = TickRecord(
                tick_number=self._tick_count,
                agent_name=self.agent.name,
                status=TickStatus.FAILED,
                timestamp=ctx.timestamp,
                duration_ms=duration_ms,
                error=str(e),
            )

        self._last_tick_time = now
        self._record(record)
        return record

    # ── Continuous loop — embodied runtime (future) ───────────────────────────

    async def run_at(
        self,
        hz: float,
        state_fn: Any = None,       # callable that returns fresh state each tick
        max_ticks: Optional[int] = None,
        on_tick: Optional[Any] = None,  # callback(record) after each tick
    ) -> None:
        """
        Run the agent continuously at a fixed tick rate.

        Args:
            hz:         Ticks per second (e.g. 10 = 100ms per cycle)
            state_fn:   Callable returning the current world state each tick.
                        If None, passes an empty dict — useful for testing.
            max_ticks:  Stop after N ticks. None = run forever.
            on_tick:    Optional async callback called after each tick.

        Usage:
            # run a perception-action loop at 10Hz
            async def get_state():
                return await sensor_bus.read()

            await ticker.run_at(hz=10, state_fn=get_state)
        """
        self._running = True
        interval = 1.0 / hz

        try:
            while self._running:
                if max_ticks and self._tick_count >= max_ticks:
                    break

                cycle_start = time.perf_counter()

                state = await state_fn() if state_fn else {}
                record = await self.tick(state)

                if on_tick:
                    if asyncio.iscoroutinefunction(on_tick):
                        await on_tick(record)
                    else:
                        on_tick(record)

                # sleep only for remaining time in the interval
                # if tick took longer than interval, skip sleep entirely
                elapsed = time.perf_counter() - cycle_start
                sleep_for = max(0.0, interval - elapsed)
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)

        finally:
            self._running = False

    def stop(self) -> None:
        """Stop a running run_at() loop gracefully."""
        self._running = False

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def last_record(self) -> Optional[TickRecord]:
        return self._history[-1] if self._history else None

    def history(self, limit: int = 10) -> list[TickRecord]:
        return self._history[-limit:]

    def success_rate(self) -> float:
        if not self._history:
            return 0.0
        successes = sum(1 for r in self._history if r.status == TickStatus.SUCCESS)
        return successes / len(self._history)

    def avg_duration_ms(self) -> float:
        if not self._history:
            return 0.0
        return sum(r.duration_ms for r in self._history) / len(self._history)

    def _record(self, record: TickRecord) -> None:
        self._history.append(record)
        if len(self._history) > self.max_history:
            self._history.pop(0)

    def __repr__(self):
        return (
            f"Ticker(agent={self.agent.name}, "
            f"ticks={self._tick_count}, "
            f"success_rate={self.success_rate():.0%})"
        )