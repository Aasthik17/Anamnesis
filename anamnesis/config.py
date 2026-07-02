import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_CONFIG = {
    "version": "0.1.0",
    "storage_dir": ".anamnesis",
    "hooks_installed": False,
    "max_context_diffs": 5,
    "reflection_threshold": 3,
    "cognee_api_key": None,
    "cognee_api_url": "https://api.cognee.ai",
    "llm_provider": "openai",
    "llm_api_key": None,
    "use_cloud": False,
}

def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Find the root directory of the repository (where .git or .anamnesis resides)."""
    current = (start_path or Path.cwd()).resolve()
    for dir_path in [current] + list(current.parents):
        if (dir_path / ".git").exists() or (dir_path / ".anamnesis").exists():
            return dir_path
    return current

def get_anamnesis_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or find_project_root()
    anamnesis_dir = root / ".anamnesis"
    anamnesis_dir.mkdir(parents=True, exist_ok=True)
    return anamnesis_dir

def get_config_path(repo_root: Optional[Path] = None) -> Path:
    return get_anamnesis_dir(repo_root) / "config.json"

def load_config(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    config_path = get_config_path(repo_root)
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any], repo_root: Optional[Path] = None) -> None:
    config_path = get_config_path(repo_root)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
