"""Round-trip and validation checks for saved TerraSim run records."""
import json

import pytest

from backend.services.run_manifest import (
    RunManifestError,
    build_run_manifest,
    load_run_manifest,
    save_run_manifest,
)


def _manifest(**overrides):
    payload = {
        "inputs": [
            {
                "path": "dem.tif",
                "role": "elevation",
                "metadata": {"width": 8, "height": 8, "crs": "EPSG:32650"},
            },
            {"path": "soil.tif", "role": "criterion", "weight": 1.0},
        ],
        "model_settings": {"alpha": 0.01, "beta": 0.02, "cfl": 0.25},
        "diagnostics": {"steps": 12, "min_stable_timestep": float("inf")},
        "outputs": {"elevation": None, "susceptibility": "susceptibility.tif"},
        "project_path": "project.terrasim.json",
        "created_at": "2026-10-24T00:00:00+00:00",
    }
    payload.update(overrides)
    return build_run_manifest(**payload)


def test_run_manifest_round_trip_is_json_safe_and_keeps_provenance(tmp_path):
    path = tmp_path / "run.terrasim-run.json"
    payload = _manifest()

    saved_path = save_run_manifest(path, payload)
    reopened = load_run_manifest(saved_path)

    assert reopened == payload
    assert reopened["format"] == "terrasim-run"
    assert reopened["diagnostics"]["min_stable_timestep"] is None
    assert reopened["coefficient_provenance"].startswith("User-supplied or exploratory")
    assert json.loads(path.read_text(encoding="utf-8")) == payload


@pytest.mark.parametrize(
    "inputs, message",
    [
        ([], "raster inputs"),
        ([{"path": "soil.tif", "role": "criterion"}], "include a DEM"),
    ],
)
def test_run_manifest_rejects_incomplete_records(inputs, message):
    with pytest.raises(RunManifestError, match=message):
        build_run_manifest(
            inputs=inputs,
            model_settings={"alpha": 0.01},
            diagnostics={"steps": 1},
        )


def test_run_manifest_rejects_unsupported_version(tmp_path):
    payload = _manifest()
    payload["version"] = 99

    with pytest.raises(RunManifestError, match="unsupported TerraSim run record version"):
        save_run_manifest(tmp_path / "future.json", payload)


def test_run_manifest_rejects_corrupt_file(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(RunManifestError, match="not valid JSON"):
        load_run_manifest(path)
