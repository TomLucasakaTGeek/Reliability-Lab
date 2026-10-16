"""Append-only JSONL spans with actual timing and conservative error messages."""

from contextlib import contextmanager
from collections.abc import Callable
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter, sleep
from typing import Iterator
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceWriter:
    def __init__(self, path: Path, run_id: str, provider_id: str, *,
                 on_update: Callable[[dict | None], None] | None = None,
                 step_delay: float = 0):
        self.path = path
        self.run_id = run_id
        self.provider_id = provider_id
        self.dataset_hash: str | None = None
        self.dataset_id: str | None = None
        self.schema_version: str | None = None
        self.events: list[dict] = []
        self.on_update = on_update
        self.step_delay = step_delay
        # Exclusive creation guards against accidental trace overwrite.
        path.touch(exist_ok=False)

    @contextmanager
    def step(self, name: str, case_id: str | None = None) -> Iterator[dict]:
        event = {"span_id": uuid4().hex, "run_id": self.run_id,
                 "case_id": case_id, "step": name, "started_at": utc_now(),
                 "status": "pass", "error_type": None, "error_message": None}
        if self.on_update:
            self.on_update({**event, "status": "running", "duration_ms": None})
        # Optional presentation pacing is separate from measured computation.
        if self.step_delay:
            sleep(self.step_delay)
        event["started_at"] = utc_now()
        start = perf_counter()
        try:
            yield event
        except Exception as exc:
            event.update(status="error", error_type=type(exc).__name__,
                         error_message=f"{name} raised {type(exc).__name__}; exception text omitted.")
            raise
        finally:
            event.update(ended_at=utc_now(), duration_ms=(perf_counter() - start) * 1000,
                         dataset_hash=self.dataset_hash, dataset_id=self.dataset_id,
                         schema_version=self.schema_version, provider_id=self.provider_id)
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            self.events.append(event)
            if self.on_update:
                self.on_update(None)
