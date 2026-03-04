from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {"int", "float", "str", "bool", "path", "enum"}


class ManifestValidationError(ValueError):
    """Raised when the manifest is malformed."""


@dataclass(frozen=True)
class ParameterDefinition:
    name: str
    type: str
    default: Any = None
    min: float | int | None = None
    max: float | int | None = None
    step: float | int | None = None
    enum: list[str] | None = None


@dataclass(frozen=True)
class FilterDefinition:
    id: str
    name: str
    script_path: str
    category: str
    tags: list[str]
    parameters: list[ParameterDefinition]
    output: dict[str, Any]


@dataclass(frozen=True)
class FilterManifest:
    version: int
    filters: list[FilterDefinition]

    def by_id(self, filter_id: str) -> FilterDefinition | None:
        return next((f for f in self.filters if f.id == filter_id), None)


def _validate_parameter(raw: dict[str, Any], filter_id: str) -> ParameterDefinition:
    name = raw.get("name")
    param_type = raw.get("type")
    if not isinstance(name, str) or not name:
        raise ManifestValidationError(f"{filter_id}: invalid parameter name")
    if param_type not in ALLOWED_TYPES:
        raise ManifestValidationError(f"{filter_id}:{name}: unsupported type {param_type!r}")

    enum_values = raw.get("enum")
    if param_type == "enum":
        if not isinstance(enum_values, list) or not enum_values or not all(isinstance(v, str) for v in enum_values):
            raise ManifestValidationError(f"{filter_id}:{name}: enum must provide non-empty string list")

    min_value = raw.get("min")
    max_value = raw.get("max")
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ManifestValidationError(f"{filter_id}:{name}: min cannot exceed max")

    return ParameterDefinition(
        name=name,
        type=param_type,
        default=raw.get("default"),
        min=min_value,
        max=max_value,
        step=raw.get("step"),
        enum=enum_values,
    )


def _validate_filter(raw: dict[str, Any], seen_ids: set[str], repo_root: Path) -> FilterDefinition:
    filter_id = raw.get("id")
    if not isinstance(filter_id, str) or not filter_id:
        raise ManifestValidationError("filter id must be a non-empty string")
    if filter_id in seen_ids:
        raise ManifestValidationError(f"duplicate filter id: {filter_id}")
    seen_ids.add(filter_id)

    name = raw.get("name")
    script_path = raw.get("script_path")
    category = raw.get("category")
    tags = raw.get("tags")
    parameters = raw.get("parameters")
    output = raw.get("output")

    if not isinstance(name, str) or not name:
        raise ManifestValidationError(f"{filter_id}: name must be non-empty string")
    if not isinstance(script_path, str) or not script_path:
        raise ManifestValidationError(f"{filter_id}: script_path must be non-empty string")
    if not (repo_root / script_path).exists():
        raise ManifestValidationError(f"{filter_id}: script_path does not exist: {script_path}")
    if not isinstance(category, str) or not category:
        raise ManifestValidationError(f"{filter_id}: category must be non-empty string")
    if not isinstance(tags, list) or not all(isinstance(t, str) and t for t in tags):
        raise ManifestValidationError(f"{filter_id}: tags must be list[str]")
    if not isinstance(parameters, list) or not parameters:
        raise ManifestValidationError(f"{filter_id}: parameters must be non-empty list")
    if not isinstance(output, dict):
        raise ManifestValidationError(f"{filter_id}: output must be object")
    preview = output.get("preview_safe_limits")
    if not isinstance(preview, dict):
        raise ManifestValidationError(f"{filter_id}: output.preview_safe_limits must be object")

    parsed_params = [_validate_parameter(p, filter_id) for p in parameters]
    names = [p.name for p in parsed_params]
    if len(names) != len(set(names)):
        raise ManifestValidationError(f"{filter_id}: duplicate parameter names")

    return FilterDefinition(
        id=filter_id,
        name=name,
        script_path=script_path,
        category=category,
        tags=tags,
        parameters=parsed_params,
        output=output,
    )


def load_manifest(path: str | Path | None = None) -> FilterManifest:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = Path(path) if path else repo_root / "filters.json"

    with manifest_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ManifestValidationError("manifest root must be object")
    version = raw.get("version")
    if not isinstance(version, int):
        raise ManifestValidationError("version must be an integer")

    filters = raw.get("filters")
    if not isinstance(filters, list):
        raise ManifestValidationError("filters must be a list")

    seen_ids: set[str] = set()
    parsed_filters = [_validate_filter(item, seen_ids, repo_root) for item in filters]
    return FilterManifest(version=version, filters=parsed_filters)
