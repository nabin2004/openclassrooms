from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Mapping, Sequence

from amoeba.exceptions import SubprocessError


@dataclass(frozen=True, slots=True)
class SubprocessResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


def run_subprocess(
    args: Sequence[str],
    *,
    check: bool = True,
    timeout_s: float | None = None,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
) -> SubprocessResult:
    """
    Run a subprocess with consistent capture + structured failures.

    - Always captures stdout/stderr as text.
    - When ``check=True`` and returncode != 0, raises ``SubprocessError`` with context.
    """
    cmd = [str(a) for a in args]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_s,
            cwd=cwd,
            env=dict(os.environ, **(dict(env) if env else {})),
        )
    except subprocess.TimeoutExpired as e:
        raise SubprocessError(
            "Subprocess timed out",
            context={
                "args": cmd,
                "timeout_s": timeout_s,
                "cwd": cwd,
                "stdout": (e.stdout or "")[:2000],
                "stderr": (e.stderr or "")[:2000],
            },
            retryable=False,
            user_message="A required external tool timed out.",
        ) from e
    except OSError as e:
        raise SubprocessError(
            "Failed to start subprocess",
            context={
                "args": cmd,
                "cwd": cwd,
                "error": repr(e),
            },
            retryable=False,
            user_message="A required external tool could not be started.",
        ) from e

    result = SubprocessResult(
        args=cmd,
        returncode=int(r.returncode),
        stdout=r.stdout or "",
        stderr=r.stderr or "",
    )

    if check and result.returncode != 0:
        raise SubprocessError(
            "Subprocess returned non-zero exit code",
            context={
                "args": cmd,
                "returncode": result.returncode,
                "cwd": cwd,
                "stdout": result.stdout[:4000],
                "stderr": result.stderr[:4000],
            },
            retryable=False,
            user_message="A required external tool failed.",
        )

    return result

