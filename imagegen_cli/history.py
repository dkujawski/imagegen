from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobMetadata:
    timestamp: str
    tool_version: str
    filter_id: str
    resolved_parameters: dict[str, Any]
    commands: list[list[str]]
    seed_fields: dict[str, Any]
    source_script: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "tool_version": self.tool_version,
            "filter_id": self.filter_id,
            "resolved_parameters": self.resolved_parameters,
            "commands": self.commands,
            "seed_fields": self.seed_fields,
            "source_script": self.source_script,
        }


def _tool_version() -> str:
    try:
        from importlib.metadata import version

        return version("imagegen")
    except Exception:  # noqa: BLE001
        return "dev"


def _seed_fields(values: dict[str, Any]) -> dict[str, Any]:
    seed_like = {}
    for key, value in values.items():
        lowered = key.lower()
        if "seed" in lowered or "random" in lowered or "rng" in lowered:
            seed_like[key] = value
    return seed_like


def _script_details(script_path: Path) -> dict[str, Any]:
    checksum = hashlib.sha256(script_path.read_bytes()).hexdigest()
    details: dict[str, Any] = {
        "path": str(script_path),
        "sha256": checksum,
        "modified_at": datetime.fromtimestamp(script_path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }

    try:
        repo_root = Path(__file__).resolve().parents[1]
        git_rev = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        if git_rev.returncode == 0:
            details["git_revision"] = git_rev.stdout.strip()
    except Exception:  # noqa: BLE001
        pass

    return details


def build_metadata(filter_id: str, values: dict[str, Any], commands: list[list[str]], script_path: Path) -> JobMetadata:
    normalized_values = {k: str(v) if isinstance(v, Path) else v for k, v in values.items()}
    return JobMetadata(
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        tool_version=_tool_version(),
        filter_id=filter_id,
        resolved_parameters=normalized_values,
        commands=commands,
        seed_fields=_seed_fields(normalized_values),
        source_script=_script_details(script_path),
    )


def write_metadata(metadata: JobMetadata, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(metadata.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def metadata_sidecar_path(output_dir: Path, file_name: str) -> Path:
    return output_dir / f"{file_name}.json"


def load_metadata(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError("metadata root must be an object")
    return raw


def replay_from_metadata(path: Path, dry_run: bool = False) -> int:
    payload = load_metadata(path)
    commands = payload.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("metadata must include a non-empty commands list")

    for command in commands:
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise ValueError("metadata command entries must be lists of strings")
        print(shlex.join(command))
        if dry_run:
            continue
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0
