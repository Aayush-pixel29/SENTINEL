import json
from pathlib import Path
from typing import List
from sentinel.eval.models import EvalTestCase


class DatasetLoader:
    """Loads evaluation datasets from JSON files or in-memory lists."""

    @classmethod
    def load_from_file(cls, file_path: str) -> List[EvalTestCase]:
        p = Path(file_path)
        if not p.exists():
            return []
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            cases = []
            for item in data:
                cases.append(EvalTestCase.model_validate(item))
            return cases

    @classmethod
    def load_default_cases(cls) -> List[EvalTestCase]:
        dataset_path = Path(__file__).parent / "datasets" / "default_cases.json"
        if dataset_path.exists():
            return cls.load_from_file(str(dataset_path))
        return []

    @classmethod
    def load_redteam_cases(cls) -> List[EvalTestCase]:
        dataset_path = Path(__file__).parent / "datasets" / "redteam_cases.json"
        if dataset_path.exists():
            return cls.load_from_file(str(dataset_path))
        return []
