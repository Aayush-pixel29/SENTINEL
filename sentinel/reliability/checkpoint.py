import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from sentinel.reliability.models import Checkpoint


class CheckpointManager:
    """Lightweight checkpoint storage for state persistence and recovery."""

    def __init__(self, base_dir: str = ".sentinel/checkpoints"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, run_id: str) -> Path:
        safe_run_id = "".join(c for c in run_id if c.isalnum() or c in ("-", "_"))
        return self.base_dir / f"{safe_run_id}.json"

    def save_checkpoint(
        self,
        run_id: str,
        state: Dict[str, Any],
        completed_step: Optional[str] = None,
        failed_step: Optional[str] = None,
        resume_from: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        existing = self.load_checkpoint(run_id)
        completed = list(existing.completed_steps) if existing else []
        if completed_step and completed_step not in completed:
            completed.append(completed_step)

        merged_state = {}
        if existing:
            merged_state.update(existing.state)
        merged_state.update(state)

        checkpoint = Checkpoint(
            run_id=run_id,
            state=merged_state,
            completed_steps=completed,
            failed_step=failed_step,
            resume_from=resume_from or failed_step,
            metadata=metadata or {},
        )

        with open(self._file_path(run_id), "w", encoding="utf-8") as f:
            f.write(checkpoint.model_dump_json(indent=2))

        return checkpoint

    def load_checkpoint(self, run_id: str) -> Optional[Checkpoint]:
        path = self._file_path(run_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return Checkpoint.model_validate_json(f.read())
        except Exception:
            return None

    def is_step_completed(self, run_id: str, step_name: str) -> bool:
        chk = self.load_checkpoint(run_id)
        if not chk:
            return False
        return step_name in chk.completed_steps

    def get_step_output(self, run_id: str, step_name: str) -> Any:
        chk = self.load_checkpoint(run_id)
        if not chk:
            return None
        return chk.state.get(step_name)
