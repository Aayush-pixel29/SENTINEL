from pathlib import Path
from sentinel.events import EventRecorder, EventStore, EventType, EventStatus, generate_run_id


def test_generate_run_id():
    rid = generate_run_id()
    assert rid.startswith("run_")
    assert len(rid) > 10


def test_event_recorder_and_store(tmp_path):
    store = EventStore(base_dir=str(tmp_path / "events"))
    recorder = EventRecorder(run_id="run_test_001", store=store)

    recorder.record_event(
        event_type=EventType.RUN,
        component="cli",
        status=EventStatus.SUCCESS,
        duration_ms=45.2,
        metadata={"target": "main"},
    )

    with recorder.span(EventType.TEST, component="pytest", metadata={"suite": "unit"}) as span:
        span.metadata["tests_run"] = 12

    trace = store.get_run_trace("run_test_001")
    assert trace is not None
    assert trace.run_id == "run_test_001"
    assert len(trace.events) == 2
    assert trace.status == EventStatus.SUCCESS
    assert trace.events[0].component == "cli"
    assert trace.events[1].component == "pytest"
    assert trace.events[1].duration_ms is not None
    assert trace.events[1].duration_ms >= 0


def test_event_store_list_runs(tmp_path):
    store = EventStore(base_dir=str(tmp_path / "events"))
    r1 = EventRecorder(run_id="run_a", store=store)
    r1.record_event(EventType.RUN, "test")
    r2 = EventRecorder(run_id="run_b", store=store)
    r2.record_event(EventType.RUN, "test")

    runs = store.list_runs()
    assert "run_a" in runs
    assert "run_b" in runs
