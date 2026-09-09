import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Optional, Any

class CheckConfig(BaseModel):
    enabled: bool = True
    command: Optional[str] = None

class ChecksConfig(BaseModel):
    test: CheckConfig = CheckConfig(command="pytest")
    lint: CheckConfig = CheckConfig(command="ruff check .")
    typecheck: CheckConfig = CheckConfig(command="mypy .")
    semgrep: CheckConfig = CheckConfig()
    secrets: CheckConfig = CheckConfig()
    dependencies: CheckConfig = CheckConfig()

class ProjectConfig(BaseModel):
    name: str = "project"
    language: str = "python"
    framework: str = "fastapi"

class TaskConfig(BaseModel):
    description: str = ""

class AIConfig(BaseModel):
    enabled: bool = True

class SentinelConfig(BaseModel):
    project: ProjectConfig = ProjectConfig()
    task: TaskConfig = TaskConfig()
    checks: ChecksConfig = ChecksConfig()
    ai: AIConfig = AIConfig()

def load_config(path: str = ".sentinel/config.yml") -> SentinelConfig:
    config_path = Path(path)
    if not config_path.exists():
        return SentinelConfig()
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
            return SentinelConfig.model_validate(data)
    except Exception:
        return SentinelConfig()
