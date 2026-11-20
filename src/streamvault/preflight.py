"""Checks that run before anything else. Each problem comes with a plain fix."""
from __future__ import annotations

import importlib.metadata as md
import os
from pathlib import Path

from .config import PROJECT_ROOT, project_path


class PreflightError(RuntimeError):
    pass


def _pinned_requirements() -> dict[str, str]:
    pins = {}
    for line in (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "==" in line:
            name, version = line.split("==", 1)
            pins[name.strip()] = version.strip()
    return pins


def check_packages() -> list[str]:
    problems = []
    for name, wanted in _pinned_requirements().items():
        try:
            have = md.version(name)
        except md.PackageNotFoundError:
            problems.append(f"Library '{name}' is not installed. Run: pip install -r requirements.txt")
            continue
        if have != wanted:
            problems.append(f"Library '{name}' is version {have}, expected {wanted}. "
                            "Run: pip install -r requirements.txt")
    return problems


def check_input(cfg: dict) -> list[str]:
    path = project_path(cfg["input"]["id_list"])
    if not path.exists():
        return [f"Candidate list not found at {path}. Put id_list.csv there "
                "(or change [input] id_list in config.toml)."]
    return []


def check_token(cfg: dict) -> list[str]:
    """Is the TMDb token there? Reads .env if it exists. Never prints the token."""
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    names = cfg["api"]["token_env_vars"]
    if not any(os.environ.get(n, "").strip() for n in names):
        return [f"TMDb token missing. Copy .env.example to .env and put your token after {names[0]}= "
                "(or set the environment variable). Cached reruns don't need it."]
    return []


def run_preflight(cfg: dict, need_token: bool) -> None:
    problems = check_packages() + check_input(cfg)
    if need_token:
        problems += check_token(cfg)
    if problems:
        raise PreflightError("Pre-flight checks failed:\n  - " + "\n  - ".join(problems))
