"""Portable, validated records for completed TerraSim terrain runs."""
from __future__ import annotations

import json
import math
import os
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_MANIFEST_FORMAT = "terrasim-run"
RUN_MANIFEST_VERSION = 1


class RunManifestError(ValueError):
    """Raised when a saved run record is malformed or unsupported."""


def _json_safe(value: Any) -> Any:
    """Copy a value into JSON types and represent non-finite diagnostics as null."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise RunManifestError(f"value of type {type(value).__name__} cannot be saved in a run record")


def _validate_manifest(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RunManifestError("run record must contain a JSON object")
    if payload.get("format") != RUN_MANIFEST_FORMAT:
        raise RunManifestError("file is not a TerraSim run record")
    if payload.get("version") != RUN_MANIFEST_VERSION:
        raise RunManifestError(
            f"unsupported TerraSim run record version: {payload.get('version')!r}"
        )
    if not isinstance(payload.get("created_at"), str) or not payload["created_at"]:
        raise RunManifestError("run record is missing created_at")

    inputs = payload.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise RunManifestError("run record must include its raster inputs")
    has_dem = False
    for index, layer in enumerate(inputs):
        if not isinstance(layer, dict):
            raise RunManifestError(f"input {index + 1} must be an object")
        if layer.get("role") not in {"elevation", "criterion"}:
            raise RunManifestError(f"input {index + 1} has an invalid raster role")
        if not isinstance(layer.get("path"), str) or not layer["path"]:
            raise RunManifestError(f"input {index + 1} is missing its source path")
        if layer["role"] == "elevation":
            has_dem = True
    if not has_dem:
        raise RunManifestError("run record must include a DEM input")

    for field in ("model_settings", "diagnostics", "outputs"):
        if not isinstance(payload.get(field), dict):
            raise RunManifestError(f"run record field {field!r} must be an object")
    if not isinstance(payload.get("project_path"), (str, type(None))):
        raise RunManifestError("project_path must be a path or null")
    for name, path in payload["outputs"].items():
        if not isinstance(name, str) or not isinstance(path, (str, type(None))):
            raise RunManifestError("output entries must map names to paths or null")

    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise RunManifestError(f"run record contains a non-JSON value: {exc}") from exc
    return payload


def build_run_manifest(
    *,
    inputs: list[Mapping[str, Any]],
    model_settings: Mapping[str, Any],
    diagnostics: Mapping[str, Any],
    outputs: Mapping[str, str | None] | None = None,
    project_path: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a self-describing record without embedding raster pixel arrays."""
    timestamp = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "format": RUN_MANIFEST_FORMAT,
        "version": RUN_MANIFEST_VERSION,
        "created_at": timestamp,
        "project_path": str(project_path) if project_path is not None else None,
        "inputs": _json_safe(list(inputs)),
        "model_settings": _json_safe(dict(model_settings)),
        "diagnostics": _json_safe(dict(diagnostics)),
        "outputs": _json_safe(dict(outputs or {})),
        "coefficient_provenance": (
            "User-supplied or exploratory; no validated soil-to-alpha/beta conversion is assumed."
        ),
    }
    return _validate_manifest(payload)


def save_run_manifest(path: str | Path, payload: Mapping[str, Any]) -> str:
    """Validate and atomically write a UTF-8 run-record JSON file."""
    destination = Path(path).expanduser()
    if not destination.name:
        raise OSError("run-record path must name a file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    validated = _validate_manifest(dict(payload))
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            json.dump(validated, temporary, indent=2, allow_nan=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, destination)
    except OSError:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
        raise
    return str(destination.resolve())


def load_run_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate a TerraSim run-record JSON file."""
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunManifestError(f"run record is not valid JSON: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise RunManifestError("run record must be UTF-8 JSON") from exc
    return _validate_manifest(payload)
