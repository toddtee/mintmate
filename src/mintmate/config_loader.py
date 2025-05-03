# src/mintmate/config_loader.py

import tomli
from pathlib import Path

def load_config(path: str = "config.toml") -> dict:
    """
    Load the TOML config from the given path. If not found in the current
    working directory, attempts to load from the package root.
    """
    # 1. Check CWD
    config_path = Path(path)
    if not config_path.is_file():
        # 2. Fallback: look in the project root (one level up from this file)
        project_root = Path(__file__).parent.parent
        candidate = project_root / path
        if candidate.is_file():
            config_path = candidate
        else:
            raise FileNotFoundError(f"Could not find config file at '{path}' or '{candidate}'")

    # 3. Parse TOML
    with config_path.open("rb") as f:
        cfg = tomli.load(f)

    # 4. Ensure file_naming defaults exist
    cfg.setdefault("file_naming", {})
    fn = cfg["file_naming"]
    fn.setdefault("override_filename", "")
    fn.setdefault("term", "")
    fn.setdefault("week", "")
    fn.setdefault("template", "mintmate_puzzles_{timestamp}.xlsx")
    fn.setdefault("cleanup_screenshots", False)
    fn.setdefault("verbose", True)

    return cfg