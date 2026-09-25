from sentinel.reliability import CheckpointManager


def test_checkpoint_save_and_load(tmp_path):
    cm = CheckpointManager(base_dir=str(tmp_path / "checkpoints"))
    run_id = "run_chk_001"

    chk1 = cm.save_checkpoint(
        run_id=run_id,
        state={"step1": "completed_output"},
        completed_step="step1",
    )
    assert chk1.run_id == run_id
    assert "step1" in chk1.completed_steps
    assert cm.is_step_completed(run_id, "step1") is True
    assert cm.is_step_completed(run_id, "step2") is False

    # Save step 2
    chk2 = cm.save_checkpoint(
        run_id=run_id,
        state={"step2": "db_initialized"},
        completed_step="step2",
    )
    assert len(chk2.completed_steps) == 2
    assert cm.get_step_output(run_id, "step1") == "completed_output"
    assert cm.get_step_output(run_id, "step2") == "db_initialized"


def test_checkpoint_failure_and_resume(tmp_path):
    cm = CheckpointManager(base_dir=str(tmp_path / "checkpoints"))
    run_id = "run_chk_fail"

    cm.save_checkpoint(
        run_id=run_id,
        state={"init": "ok"},
        completed_step="init",
    )

    cm.save_checkpoint(
        run_id=run_id,
        state={},
        failed_step="api_call_external",
        resume_from="api_call_external",
    )

    loaded = cm.load_checkpoint(run_id)
    assert loaded.failed_step == "api_call_external"
    assert loaded.resume_from == "api_call_external"
    assert "init" in loaded.completed_steps
