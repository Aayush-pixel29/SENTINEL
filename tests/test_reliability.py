from sentinel.reliability import ExecutionManager, ExecutionStatus, CheckpointManager


def test_execution_manager_success():
    em = ExecutionManager()

    def add_fn(a, b):
        return a + b

    rec = em.execute_with_retry(
        run_id="run_rel_001",
        tool_name="add_numbers",
        fn=add_fn,
        args={"a": 10, "b": 25},
    )
    assert rec.status == ExecutionStatus.SUCCEEDED
    assert rec.result == 35
    assert rec.retry_count == 0


def test_execution_manager_idempotency(tmp_path):
    cm = CheckpointManager(base_dir=str(tmp_path / "checkpoints"))
    em = ExecutionManager(checkpoint_manager=cm)

    counter = {"calls": 0}

    def side_effect_fn():
        counter["calls"] += 1
        return "transaction_42"

    rec1 = em.execute_with_retry(
        run_id="run_idem_001",
        tool_name="transfer_funds",
        fn=side_effect_fn,
        args={},
        idempotency_key="tx_unique_key_999",
    )
    assert rec1.result == "transaction_42"
    assert counter["calls"] == 1
    assert rec1.cached is False

    # Second execution with same idempotency key
    rec2 = em.execute_with_retry(
        run_id="run_idem_001",
        tool_name="transfer_funds",
        fn=side_effect_fn,
        args={},
        idempotency_key="tx_unique_key_999",
    )
    assert rec2.result == "transaction_42"
    assert counter["calls"] == 1  # Function was NOT executed again
    assert rec2.cached is True


def test_execution_manager_retry_then_success():
    em = ExecutionManager()
    attempts = {"count": 0}

    def flaky_fn():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ConnectionError("Network glitch")
        return "success_after_glitch"

    rec = em.execute_with_retry(
        run_id="run_retry_001",
        tool_name="flaky_api",
        fn=flaky_fn,
        args={},
        max_retries=2,
    )
    assert rec.status == ExecutionStatus.SUCCEEDED
    assert rec.result == "success_after_glitch"
    assert rec.retry_count == 1


def test_execution_manager_max_retries_failure():
    em = ExecutionManager()

    def always_fail():
        raise ValueError("Permanent failure")

    rec = em.execute_with_retry(
        run_id="run_fail_001",
        tool_name="failing_tool",
        fn=always_fail,
        args={},
        max_retries=1,
    )
    assert rec.status == ExecutionStatus.FAILED
    assert "Permanent failure" in str(rec.error)
