import os
from pathlib import Path
from sentinel.models import VerificationReport

def generate_json_report(report: VerificationReport, output_path: str = ".sentinel/report.json"):
    """Generates the JSON report from the VerificationReport object."""
    os.makedirs(Path(output_path).parent, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
