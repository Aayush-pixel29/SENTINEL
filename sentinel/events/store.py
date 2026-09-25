import json
import os
from pathlib import Path
from typing import List, Optional
from sentinel.events.models import TraceEvent, RunTrace, EventStatus


class EventStore:
    """Local JSONL / JSON storage for Sentinel-X traces."""

    def __init__(self, base_dir: str = ".sentinel/events"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_run_file(self, run_id: str) -> Path:
        # Sanitize filename
        safe_run_id = "".join(c for c in run_id if c.isalnum() or c in ("-", "_"))
        return self.base_dir / f"{safe_run_id}.jsonl"

    def append_event(self, event: TraceEvent) -> None:
        file_path = self._get_run_file(event.run_id)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def get_events(self, run_id: str) -> List[TraceEvent]:
        file_path = self._get_run_file(run_id)
        if not file_path.exists():
            return []
        events = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(TraceEvent.model_validate_json(line))
                    except Exception:
                        pass
        return events

    def get_run_trace(self, run_id: str) -> Optional[RunTrace]:
        events = self.get_events(run_id)
        if not events:
            return None

        first_evt = events[0]
        last_evt = events[-1]

        total_duration = sum(e.duration_ms or 0.0 for e in events)
        total_in_tokens = sum(e.input_tokens or 0 for e in events)
        total_out_tokens = sum(e.output_tokens or 0 for e in events)
        total_cost = sum(e.estimated_cost_usd or 0.0 for e in events)

        # Overall status
        status = EventStatus.SUCCESS
        if any(e.status in (EventStatus.FAILURE, EventStatus.ERROR) for e in events):
            status = EventStatus.FAILURE
        elif any(e.status == EventStatus.BLOCKED for e in events):
            status = EventStatus.BLOCKED

        return RunTrace(
            run_id=run_id,
            started_at=first_evt.started_at,
            ended_at=last_evt.started_at,
            status=status,
            total_events=len(events),
            total_duration_ms=total_duration,
            total_input_tokens=total_in_tokens,
            total_output_tokens=total_out_tokens,
            total_cost_usd=round(total_cost, 6),
            events=events,
        )

    def list_runs(self) -> List[str]:
        if not self.base_dir.exists():
            return []
        return [f.stem for f in self.base_dir.glob("*.jsonl")]
