import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator, List
from sentinel.events.models import TraceEvent, EventType, EventStatus
from sentinel.events.store import EventStore


def generate_run_id(prefix: str = "run") -> str:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    rand_suffix = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{rand_suffix}"


class EventRecorder:
    """Thread-safe and process-friendly recorder for unified execution spans."""

    def __init__(self, run_id: Optional[str] = None, store: Optional[EventStore] = None):
        self.run_id = run_id or generate_run_id()
        self.store = store or EventStore()
        self._active_parent_ids: List[str] = []

    def record_event(
        self,
        event_type: EventType,
        component: str,
        status: EventStatus = EventStatus.SUCCESS,
        parent_event_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        estimated_cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> TraceEvent:
        parent = parent_event_id or (self._active_parent_ids[-1] if self._active_parent_ids else None)
        event = TraceEvent(
            run_id=self.run_id,
            parent_event_id=parent,
            event_type=event_type,
            component=component,
            status=status,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            metadata=metadata or {},
            error=error,
        )
        self.store.append_event(event)
        return event

    @contextmanager
    def span(
        self,
        event_type: EventType,
        component: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_event_id: Optional[str] = None,
    ) -> Generator[TraceEvent, None, None]:
        parent = parent_event_id or (self._active_parent_ids[-1] if self._active_parent_ids else None)
        event = TraceEvent(
            run_id=self.run_id,
            parent_event_id=parent,
            event_type=event_type,
            component=component,
            status=EventStatus.RUNNING,
            metadata=metadata or {},
        )
        self._active_parent_ids.append(event.event_id)
        start_time = time.perf_counter()
        try:
            yield event
            event.status = EventStatus.SUCCESS
        except Exception as ex:
            event.status = EventStatus.ERROR
            event.error = str(ex)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            event.duration_ms = round(elapsed_ms, 2)
            if self._active_parent_ids and self._active_parent_ids[-1] == event.event_id:
                self._active_parent_ids.pop()
            self.store.append_event(event)
