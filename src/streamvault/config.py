"""Read the settings in config.toml.
File paths are measured from the project folder, so the code works the same
on any computer (Windows, Mac or Linux) and from any folder."""
from __future__ import annotations

import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None) -> dict:
    path = path or PROJECT_ROOT / "config.toml"
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def project_path(relative: str) -> Path:
    return PROJECT_ROOT / relative
