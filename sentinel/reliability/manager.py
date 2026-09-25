import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timezone
from sentinel.reliability.models import ExecutionRecord, ExecutionStatus
from sentinel.reliability.checkpoint import CheckpointManager
from sentinel.events.recorder import EventRecorder
from sentinel.events.models import EventType, EventStatus


class ExecutionManager:
    """Local reliability and idempotency manager for tool executions."""

    def __init__(
        self,
        checkpoint_manager: Optional[CheckpointManager] = None,
        recorder: Optional[EventRecorder] = None,
    ):
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.recorder = recorder
        self._execution_history: Dict[str, ExecutionRecord] = {}
        self._idempotency_cache: Dict[str, ExecutionRecord] = {}

    def execute_with_retry(
        self,
        run_id: str,
        tool_name: str,
        fn: Callable[..., Any],
        args: Dict[str, Any],
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        idempotency_key: Optional[str] = None,
    ) -> ExecutionRecord:
        """Executes a function with duplicate protection, retry logic, and timing telemetry."""

        # 1. Duplicate execution / Idempotency protection
        if idempotency_key and idempotency_key in self._idempotency_cache:
            cached_rec = self._idempotency_cache[idempotency_key]
            if cached_rec.status == ExecutionStatus.SUCCEEDED:
                return ExecutionRecord(
                    execution_id=cached_rec.execution_id,
                    run_id=run_id,
                    tool_name=tool_name,
                    status=ExecutionStatus.SUCCEEDED,
                    arguments=args,
                    result=cached_rec.result,
                    idempotency_key=idempotency_key,
                    cached=True,
                    retry_count=0,
                )

        record = ExecutionRecord(
            run_id=run_id,
            tool_name=tool_name,
            status=ExecutionStatus.RUNNING,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            idempotency_key=idempotency_key,
            arguments=args,
        )
        self._execution_history[record.execution_id] = record

        attempts = 0
        last_error = None
        start_perf = time.perf_counter()

        while attempts <= max_retries:
            try:
                if attempts > 0:
                    record.status = ExecutionStatus.RETRYING
                    record.retry_count = attempts

                # Execute function
                result = fn(**args) if args else fn()

                record.status = ExecutionStatus.SUCCEEDED
                record.result = result
                record.end_time = datetime.now(timezone.utc).isoformat()
                record.duration_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)

                # Cache in idempotency table
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = record

                # Save checkpoint step
                self.checkpoint_manager.save_checkpoint(
                    run_id=run_id,
                    state={tool_name: result},
                    completed_step=tool_name,
                )

                if self.recorder:
                    self.recorder.record_event(
                        event_type=EventType.TOOL_CALL,
                        component="execution_manager",
                        status=EventStatus.SUCCESS,
                        duration_ms=record.duration_ms,
                        metadata={
                            "tool": tool_name,
                            "execution_id": record.execution_id,
                            "retries": record.retry_count,
                            "idempotency_key": idempotency_key,
                        },
                    )

                return record

            except Exception as ex:
                last_error = str(ex)
                attempts += 1
                if attempts <= max_retries:
                    time.sleep(0.05 * attempts)

        record.status = ExecutionStatus.FAILED
        record.error = last_error
        record.end_time = datetime.now(timezone.utc).isoformat()
        record.duration_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)

        self.checkpoint_manager.save_checkpoint(
            run_id=run_id,
            state={},
            failed_step=tool_name,
            resume_from=tool_name,
        )

        if self.recorder:
            self.recorder.record_event(
                event_type=EventType.TOOL_CALL,
                component="execution_manager",
                status=EventStatus.FAILURE,
                duration_ms=record.duration_ms,
                metadata={
                    "tool": tool_name,
                    "execution_id": record.execution_id,
                    "error": last_error,
                },
                error=last_error,
            )

        return record
