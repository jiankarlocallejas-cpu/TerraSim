"""Tests for the paper-aligned susceptibility and Exner reference model."""
import numpy as np
import pytest

from backend.services.paper_model import (
    ExnerTerrainModel,
    estimate_reference_memory_bytes,
    weighted_susceptibility_index,
)


def make_model(**overrides):
    parameters = {
        "cell_size_x": 2.0,
        "cell_size_y": 3.0,
        "alpha": 0.25,
        "beta": 0.05,
        "critical_slope_threshold": 0.02,
        "diffusion_tensor": ((1.0, 0.0), (0.0, 1.0)),
        "cfl": 0.25,
    }
    parameters.update(overrides)
    return ExnerTerrainModel(**parameters)


def test_flat_terrain_is_stationary_and_has_no_flux_response():
    model = make_model()
    result = model.step(np.full((5, 6), 100.0), timestep=1.0)

    assert np.array_equal(result.elevation, np.full((5, 6), 100.0))
    assert result.max_abs_elevation_change == 0.0
    assert result.mass_after == pytest.approx(result.mass_before)


def test_hill_evolves_and_closed_boundaries_conserve_terrain_volume():
    elevation = np.zeros((7, 7), dtype=float)
    elevation[3, 3] = 10.0
    model = make_model(alpha=0.1, beta=0.1, critical_slope_threshold=0.0)
    stable_dt = model.stable_timestep(elevation)

    result = model.step(elevation, timestep=stable_dt * 0.5)

    assert result.elevation[3, 3] < elevation[3, 3]
    assert result.max_abs_elevation_change > 0.0
    assert result.mass_after == pytest.approx(result.mass_before, abs=1e-12)


def test_nodata_cells_are_preserved_and_block_flux():
    elevation = np.zeros((7, 7), dtype=float)
    elevation[3, 2] = 2.0
    elevation[3, 3] = -9999.0
    model = make_model(alpha=0.1, beta=0.1, critical_slope_threshold=0.0, nodata=-9999.0)
    stable_dt = model.stable_timestep(elevation)
    result = model.step(elevation, timestep=stable_dt * 0.5)

    assert result.elevation[3, 3] == -9999.0
    assert not result.valid_mask[3, 3]
    assert result.valid_mask.sum() == 48
    assert result.mass_after == pytest.approx(result.mass_before, abs=1e-12)


def test_explicit_step_rejects_timestep_above_stability_limit():
    model = make_model()
    elevation = np.arange(25, dtype=float).reshape(5, 5)
    stable_dt = model.stable_timestep(elevation)

    with pytest.raises(ValueError, match="stability limit"):
        model.step(elevation, timestep=stable_dt * 1.01)


def test_simulation_substeps_to_stability_bound_without_retaining_history():
    model = make_model()
    elevation = np.arange(25, dtype=float).reshape(5, 5)
    stable_dt = model.stable_timestep(elevation)
    progress = []
    result = model.simulate(
        elevation,
        total_time=stable_dt * 2.25,
        max_timestep=stable_dt * 0.5,
        progress=lambda steps, elapsed, dt: progress.append((steps, elapsed, dt)),
    )

    assert result.elapsed_time == pytest.approx(stable_dt * 2.25)
    assert result.step_count == len(progress)
    assert result.step_count >= 5
    assert result.mass_after == pytest.approx(result.mass_before, abs=1e-10)


def test_alpha_threshold_and_beta_control_transport_response():
    rows, cols = np.mgrid[0:7, 0:7]
    plane = -0.1 * cols.astype(float)

    below_threshold = make_model(
        alpha=1.0, beta=0.0, critical_slope_threshold=0.02
    )
    assert np.array_equal(
        below_threshold.step(plane, timestep=1.0).elevation,
        plane,
    )

    alpha_active = make_model(
        alpha=1.0, beta=0.0, critical_slope_threshold=0.001
    )
    active_dt = alpha_active.stable_timestep(plane)
    alpha_result = alpha_active.step(plane, active_dt * 0.5)
    assert alpha_result.max_abs_elevation_change > 0.0

    beta_active = make_model(
        alpha=0.0, beta=0.1, critical_slope_threshold=2.0
    )
    beta_dt = beta_active.stable_timestep(plane)
    beta_result = beta_active.step(plane, beta_dt * 0.5)
    assert beta_result.max_abs_elevation_change > 0.0


def test_anisotropic_diffusion_tensor_is_supported():
    elevation = np.zeros((7, 7), dtype=float)
    elevation[3, 3] = 5.0
    model = make_model(
        alpha=0.0,
        beta=0.1,
        critical_slope_threshold=10.0,
        diffusion_tensor=((2.0, 0.25), (0.25, 1.0)),
    )
    dt = model.stable_timestep(elevation)
    result = model.step(elevation, dt * 0.5)

    assert result.max_abs_elevation_change > 0.0
    assert result.mass_after == pytest.approx(result.mass_before, abs=1e-12)


@pytest.mark.parametrize(
    "overrides",
    [
        {"cell_size_x": 0.0},
        {"alpha": -0.1},
        {"beta": float("inf")},
        {"critical_slope_threshold": -1.0},
        {"cfl": 0.0},
        {"diffusion_tensor": ((1.0, 1.0), (0.0, 1.0))},
        {"diffusion_tensor": ((1.0, 0.0), (0.0, 0.0))},
    ],
)
def test_model_rejects_invalid_parameters(overrides):
    with pytest.raises(ValueError):
        make_model(**overrides)


def test_mce_overlay_uses_explicit_normalized_weights_and_preserves_nodata():
    index = weighted_susceptibility_index(
        {
            "rainfall": np.array([[0.0, 1.0], [np.nan, 0.5]]),
            "soil": np.array([[1.0, 0.0], [0.5, 0.5]]),
        },
        {"rainfall": 0.25, "soil": 0.75},
    )

    assert index[0, 0] == pytest.approx(0.75)
    assert index[0, 1] == pytest.approx(0.25)
    assert np.isnan(index[1, 0])
    assert index[1, 1] == pytest.approx(0.5)


def test_mce_overlay_rejects_unproven_normalization_and_weight_sums():
    with pytest.raises(ValueError, match="sum to 1"):
        weighted_susceptibility_index(
            {"a": np.ones((2, 2))}, {"a": 0.5}
        )
    with pytest.raises(ValueError, match=r"normalized to \[0, 1\]"):
        weighted_susceptibility_index(
            {"a": np.array([[2.0]])}, {"a": 1.0}
        )


def test_mce_overlay_checks_shapes_and_applies_valid_mask():
    criteria = {"a": np.array([[0.2, 0.3]]), "b": np.array([[0.8, 0.9]])}
    result = weighted_susceptibility_index(
        criteria, {"a": 0.5, "b": 0.5}, valid_mask=np.array([[True, False]])
    )

    assert result[0, 0] == pytest.approx(0.5)
    assert np.isnan(result[0, 1])
    with pytest.raises(ValueError, match="different grid shape"):
        weighted_susceptibility_index(
            {"a": np.ones((1, 2)), "b": np.ones((2, 1))},
            {"a": 0.5, "b": 0.5},
        )




def test_simulation_can_cancel_between_substeps():
    model = make_model()
    elevation = np.arange(25, dtype=float).reshape(5, 5)
    stable_dt = model.stable_timestep(elevation)
    progress = []
    result = model.simulate(
        elevation,
        total_time=stable_dt * 10,
        max_timestep=stable_dt * 0.5,
        progress=lambda steps, elapsed, dt: progress.append((steps, elapsed, dt)),
        cancel_requested=lambda: len(progress) >= 2,
    )

    assert result.cancelled
    assert result.step_count == 2
    assert result.elapsed_time < stable_dt * 10



@pytest.mark.parametrize(
    ("width", "height", "criterion_count", "expected"),
    [(10, 20, 0, 51200), (10, 20, 2, 54400)],
)
def test_reference_memory_estimate(width, height, criterion_count, expected):
    assert estimate_reference_memory_bytes(width, height, criterion_count) == expected


@pytest.mark.parametrize(
    ("width", "height", "criterion_count"),
    [(0, 1, 0), (1, 0, 0), (1, 1, -1)],
)
def test_reference_memory_estimate_rejects_invalid_dimensions(
    width, height, criterion_count
):
    with pytest.raises(ValueError):
        estimate_reference_memory_bytes(width, height, criterion_count)

