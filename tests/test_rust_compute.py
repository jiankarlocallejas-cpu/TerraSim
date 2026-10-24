"""Parity tests run when the optional maturin extension is installed."""
import numpy as np
import pytest

pytest.importorskip("terrasim_compute")

from terrasim_compute import evaluate_flux_divergence
import backend.services.paper_model as paper_model
from backend.services.paper_model import ExnerTerrainModel


def test_rust_flux_kernel_matches_python_reference(monkeypatch):
    elevation = np.array(
        [
            [0.0, 1.0, 3.0, 4.0],
            [1.5, 99.0, 2.5, 5.0],
            [0.5, 2.0, 3.5, 7.0],
        ],
        dtype=np.float64,
    )
    valid = np.array(
        [[1, 1, 1, 1], [1, 0, 1, 1], [1, 1, 1, 1]],
        dtype=bool,
    )
    model = ExnerTerrainModel(
        cell_size_x=30.0,
        cell_size_y=20.0,
        alpha=0.02,
        beta=0.002,
        critical_slope_threshold=0.1,
        diffusion_tensor=np.array([[1.2, 0.15], [0.15, 0.8]]),
        cfl=0.25,
    )

    monkeypatch.setattr(paper_model, "_rust_evaluate_flux_divergence", None)
    expected_divergence, expected_timestep = model._evaluate(elevation, valid)
    actual_divergence, actual_timestep = evaluate_flux_divergence(
        elevation,
        valid,
        model.cell_size_x,
        model.cell_size_y,
        model.alpha,
        model.beta,
        model.critical_slope_threshold,
        model.diffusion_tensor[0, 0],
        model.diffusion_tensor[0, 1],
        model.diffusion_tensor[1, 1],
        model.cfl,
    )

    np.testing.assert_allclose(actual_divergence, expected_divergence, rtol=1e-12, atol=1e-14)
    assert actual_timestep == pytest.approx(expected_timestep, rel=1e-12)

