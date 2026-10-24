"""Compare one synthetic multi-step run with the Python and optional Rust kernels."""
from __future__ import annotations

import json
import time

import numpy as np

import backend.services.paper_model as paper_model
from backend.services.paper_model import ExnerTerrainModel


def main() -> None:
    rust_kernel = paper_model._rust_evaluate_flux_divergence
    if rust_kernel is None:
        raise SystemExit("Install ./rust/terrasim_compute before running this benchmark.")

    size = 1024
    axis = np.arange(size, dtype=np.float32)
    elevation = (
        100.0
        + 0.01
        * (np.sin(axis[:, None] / 40.0) + np.cos(axis[None, :] / 35.0))
    ).astype(np.float32)
    model = ExnerTerrainModel(
        cell_size_x=30.0,
        cell_size_y=30.0,
        alpha=0.01,
        beta=0.01,
        critical_slope_threshold=0.0,
    )

    try:
        paper_model._rust_evaluate_flux_divergence = None
        started = time.perf_counter()
        python_result = model.simulate(elevation, total_time=5.0, max_timestep=0.5)
        python_seconds = time.perf_counter() - started

        paper_model._rust_evaluate_flux_divergence = rust_kernel
        started = time.perf_counter()
        rust_result = model.simulate(elevation, total_time=5.0, max_timestep=0.5)
        rust_seconds = time.perf_counter() - started
    finally:
        paper_model._rust_evaluate_flux_divergence = rust_kernel

    np.testing.assert_allclose(
        rust_result.elevation, python_result.elevation, rtol=1e-12, atol=1e-12
    )
    assert rust_result.step_count == python_result.step_count
    assert abs(rust_result.mass_after - python_result.mass_after) < 1e-8
    print(
        json.dumps(
            {
                "grid": [size, size],
                "steps": rust_result.step_count,
                "python_seconds": round(python_seconds, 3),
                "rust_seconds": round(rust_seconds, 3),
                "speedup": round(python_seconds / rust_seconds, 2),
                "max_abs_output_difference": float(
                    np.max(np.abs(rust_result.elevation - python_result.elevation))
                ),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

